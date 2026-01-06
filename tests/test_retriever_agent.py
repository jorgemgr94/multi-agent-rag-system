"""Tests for the RetrieverAgent."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.agents.retriever import (
    DEFAULT_TOP_K,
    MAX_CONTEXT_TOKENS,
    MAX_TOP_K,
    MIN_RELEVANCE_SCORE,
    MIN_TOP_K,
    RetrievalObservation,
    RetrievalResult,
    RetrieverAgent,
)
from app.schemas.document import SearchQuery, SearchResponse, SearchResult
from app.schemas.task import DecisionType, TaskInput

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = MagicMock()
    store.count = 100

    # Default search response
    store.search.return_value = SearchResponse(
        results=[
            SearchResult(
                content="MedTech Inc deal closed at $75K. Healthcare industry.",
                score=0.92,
                metadata={
                    "doc_id": "deal_001",
                    "doc_type": "deal",
                    "source_file": "deals/deal_001.md",
                    "chunk_index": 0,
                },
            ),
            SearchResult(
                content="Healthcare playbook: Focus on compliance and HIPAA.",
                score=0.85,
                metadata={
                    "doc_id": "healthcare_playbook",
                    "doc_type": "industry",
                    "source_file": "industries/healthcare_playbook.md",
                    "chunk_index": 0,
                },
            ),
        ],
        total_searched=100,
        query="healthcare deals",
    )

    return store


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for query rewriting."""
    response = MagicMock()
    response.content = "healthcare sector deals closed successfully"
    return response


@pytest.fixture
def retriever_agent(mock_vector_store, mock_llm_response):
    """Create a RetrieverAgent with mocked dependencies."""
    with patch("app.agents.retriever.ChatOpenAI") as mock_chat:
        mock_chat.return_value.invoke.return_value = mock_llm_response
        agent = RetrieverAgent(vector_store=mock_vector_store)
        agent.llm.invoke = MagicMock(return_value=mock_llm_response)
        return agent


# =============================================================================
# RetrievalResult Tests
# =============================================================================


class TestRetrievalResult:
    """Tests for RetrievalResult schema."""

    def test_from_search_result(self):
        """Test conversion from SearchResult."""
        search_result = SearchResult(
            content="Test content",
            score=0.9,
            metadata={
                "doc_id": "test_doc",
                "doc_type": "deal",
                "source_file": "deals/test.md",
                "chunk_index": 2,
            },
        )

        result = RetrievalResult.from_search_result(search_result)

        assert result.content == "Test content"
        assert result.score == 0.9
        assert result.doc_id == "test_doc"
        assert result.doc_type == "deal"
        assert result.source_file == "deals/test.md"
        assert result.chunk_index == 2


# =============================================================================
# RetrieverAgent Tests
# =============================================================================


class TestRetrieverAgent:
    """Tests for RetrieverAgent."""

    def test_agent_initialization(self, mock_vector_store):
        """Test agent initializes correctly."""
        with patch("app.agents.retriever.ChatOpenAI"):
            agent = RetrieverAgent(vector_store=mock_vector_store)

            assert agent.name == "retriever"
            assert agent.vector_store == mock_vector_store
            assert agent.max_context_tokens == MAX_CONTEXT_TOKENS

    def test_agent_custom_max_tokens(self, mock_vector_store):
        """Test agent with custom token limit."""
        with patch("app.agents.retriever.ChatOpenAI"):
            agent = RetrieverAgent(
                vector_store=mock_vector_store,
                max_context_tokens=2000,
            )

            assert agent.max_context_tokens == 2000

    def test_count_tokens(self, retriever_agent):
        """Test token counting."""
        tokens = retriever_agent.count_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 10  # Simple phrase

    def test_reason_returns_retrieve_decision(self, retriever_agent):
        """Test that reason() returns a RETRIEVE decision."""
        task_input = TaskInput(task="Find healthcare deals")

        decision = retriever_agent.reason(task_input)

        assert decision.decision_type == DecisionType.RETRIEVE
        assert decision.tool_call is not None
        assert decision.tool_call.tool_name == "vector_search"
        assert "Retrieved" in decision.reasoning

    def test_reason_with_filters(self, retriever_agent):
        """Test reason() passes filters correctly."""
        task_input = TaskInput(
            task="Find won deals",
            context={"filters": {"outcome": "won"}},
        )

        decision = retriever_agent.reason(task_input)

        assert decision.tool_call.arguments["filters"] == {"outcome": "won"}

    def test_reason_with_custom_top_k(self, retriever_agent):
        """Test reason() respects custom top_k."""
        task_input = TaskInput(
            task="Find deals",
            context={"top_k": 3},
        )

        decision = retriever_agent.reason(task_input)

        assert decision.tool_call.arguments["top_k"] == 3


class TestRetrieverAgentRetrieve:
    """Tests for the retrieve() method."""

    def test_retrieve_returns_observation(self, retriever_agent):
        """Test that retrieve() returns a RetrievalObservation."""
        observation = retriever_agent.retrieve("healthcare deals")

        assert isinstance(observation, RetrievalObservation)
        assert observation.query == "healthcare deals"
        assert len(observation.results) > 0

    def test_retrieve_filters_low_relevance(self, retriever_agent, mock_vector_store):
        """Test that low-relevance results are filtered out."""
        # Add a low-score result
        mock_vector_store.search.return_value = SearchResponse(
            results=[
                SearchResult(
                    content="High relevance content",
                    score=0.9,
                    metadata={
                        "doc_id": "high",
                        "doc_type": "deal",
                        "source_file": "deals/high.md",
                    },
                ),
                SearchResult(
                    content="Low relevance content",
                    score=0.3,  # Below MIN_RELEVANCE_SCORE
                    metadata={
                        "doc_id": "low",
                        "doc_type": "deal",
                        "source_file": "deals/low.md",
                    },
                ),
            ],
            total_searched=100,
            query="test",
        )

        observation = retriever_agent.retrieve("test query")

        # Only high relevance result should be included
        assert len(observation.results) == 1
        assert observation.results[0].doc_id == "high"

    def test_retrieve_clamps_top_k(self, retriever_agent, mock_vector_store):
        """Test that top_k is clamped to valid range."""
        # Test minimum
        retriever_agent.retrieve("test", top_k=0)
        call_args = mock_vector_store.search.call_args
        assert call_args[0][0].top_k >= MIN_TOP_K

        # Test maximum
        retriever_agent.retrieve("test", top_k=100)
        call_args = mock_vector_store.search.call_args
        assert call_args[0][0].top_k <= MAX_TOP_K

    def test_retrieve_tracks_sources(self, retriever_agent):
        """Test that results include source tracking."""
        observation = retriever_agent.retrieve("healthcare")

        for result in observation.results:
            assert result.doc_id is not None
            assert result.doc_type is not None
            assert result.source_file is not None


class TestQueryRewriting:
    """Tests for query rewriting functionality."""

    def test_short_query_not_rewritten(self, retriever_agent):
        """Test that very short queries skip rewriting."""
        # Short queries (2 words or less) should not be rewritten
        rewritten = retriever_agent._rewrite_query("deals")

        assert rewritten == "deals"

    def test_query_rewriting_uses_llm(self, retriever_agent, mock_llm_response):
        """Test that longer queries use LLM for rewriting."""
        # Ensure the mock returns a valid string
        mock_llm_response.content = "optimized healthcare deals query"
        retriever_agent.llm.invoke = MagicMock(return_value=mock_llm_response)

        rewritten = retriever_agent._rewrite_query(
            "show me healthcare deals that we won"
        )

        assert rewritten == "optimized healthcare deals query"
        retriever_agent.llm.invoke.assert_called_once()


class TestContextWindowManagement:
    """Tests for context window token management."""

    def test_select_within_token_limit(self, retriever_agent):
        """Test that results are selected within token limit."""
        # Create results with known token counts
        results = [
            SearchResult(
                content="Short content",  # ~2-3 tokens
                score=0.9,
                metadata={"doc_id": "1", "doc_type": "deal", "source_file": "1.md"},
            ),
            SearchResult(
                content="A " * 2000,  # ~2000 tokens, should exceed limit
                score=0.8,
                metadata={"doc_id": "2", "doc_type": "deal", "source_file": "2.md"},
            ),
        ]

        # Set a low token limit
        retriever_agent.max_context_tokens = 100

        selected = retriever_agent._select_within_token_limit(results)

        # Should only include the first result
        assert len(selected) == 1
        assert selected[0].metadata["doc_id"] == "1"

    def test_empty_results_handled(self, retriever_agent):
        """Test that empty results are handled gracefully."""
        selected = retriever_agent._select_within_token_limit([])
        assert selected == []


class TestObservationFormatting:
    """Tests for observation and context formatting."""

    def test_to_observation(self, retriever_agent):
        """Test conversion to standard Observation."""
        retrieval = RetrievalObservation(
            query="test query",
            rewritten_query="optimized test query",
            results=[
                RetrievalResult(
                    content="Test content",
                    score=0.9,
                    doc_id="test",
                    doc_type="deal",
                    source_file="test.md",
                    chunk_index=0,
                )
            ],
            total_results=1,
            total_tokens=10,
        )

        observation = retriever_agent.to_observation(retrieval)

        assert observation.source == "retrieval"
        assert observation.success is True
        assert observation.result["query"] == "test query"
        assert observation.result["total_results"] == 1

    def test_format_context(self, retriever_agent):
        """Test formatting retrieval as context string."""
        retrieval = RetrievalObservation(
            query="test",
            rewritten_query="test",
            results=[
                RetrievalResult(
                    content="Test content here",
                    score=0.9,
                    doc_id="test",
                    doc_type="deal",
                    source_file="deals/test.md",
                    chunk_index=0,
                )
            ],
            total_results=1,
            total_tokens=10,
        )

        context = retriever_agent.format_context(retrieval)

        assert "Source 1: deals/test.md" in context
        assert "Test content here" in context
        assert "Relevance: 0.90" in context
        assert "Retrieved 1 relevant documents" in context

    def test_format_context_empty(self, retriever_agent):
        """Test formatting when no results."""
        retrieval = RetrievalObservation(
            query="test",
            rewritten_query="test",
            results=[],
            total_results=0,
            total_tokens=0,
        )

        context = retriever_agent.format_context(retrieval)

        assert "No relevant documents found" in context
