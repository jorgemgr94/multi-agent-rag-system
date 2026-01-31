"""Tests for briefing agents and orchestration."""

from unittest.mock import MagicMock, patch

import pytest

from app.briefings.agents import (
    CompanyResearcherAgent,
    CompetitorAnalystAgent,
    OrchestratorAgent,
    ProposalDrafterAgent,
    SimilarDealsFinderAgent,
    SpecialistResult,
)
from app.briefings.schemas import BriefingRequest
from app.documents.schemas import RetrievalObservation, RetrievalResult

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_retriever():
    """Create a mock retriever agent."""
    retriever = MagicMock()
    retriever.vector_store = MagicMock()
    retriever.vector_store.count = 50

    # Default retrieval response
    retriever.retrieve.return_value = RetrievalObservation(
        query="test query",
        rewritten_query="test query",
        results=[
            RetrievalResult(
                content="Sample content about healthcare deals",
                score=0.9,
                doc_id="doc_001",
                doc_type="deal",
                source_file="deals/deal_001.md",
                chunk_index=0,
            )
        ],
        total_results=1,
        total_tokens=50,
    )

    return retriever


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    response = MagicMock()
    response.content = """{
        "overview": "Test overview",
        "key_priorities": ["Priority 1", "Priority 2"],
        "relevant_trends": ["Trend 1"],
        "considerations": ["Consider this"]
    }"""
    return response


# =============================================================================
# Specialist Agent Tests
# =============================================================================


class TestCompanyResearcherAgent:
    """Tests for CompanyResearcherAgent."""

    def test_initialization(self, mock_retriever):
        """Test agent initializes correctly."""
        with patch("app.briefings.agents.base.ChatOpenAI"):
            agent = CompanyResearcherAgent(retriever=mock_retriever)

        assert agent.name == "company_researcher"
        assert "industry" in agent.retrieval_filters.get("doc_type", "")

    def test_execute_returns_result(self, mock_retriever, mock_llm_response):
        """Test execute returns a SpecialistResult."""
        with patch("app.briefings.agents.base.ChatOpenAI") as mock_chat:
            mock_chat.return_value.invoke.return_value = mock_llm_response
            agent = CompanyResearcherAgent(retriever=mock_retriever)
            agent.llm.invoke = MagicMock(return_value=mock_llm_response)

            result = agent.execute(
                {"company_name": "Test Corp", "industry": "healthcare"}
            )

        assert isinstance(result, SpecialistResult)
        assert result.agent_name == "company_researcher"
        assert result.success is True


class TestSimilarDealsFinderAgent:
    """Tests for SimilarDealsFinderAgent."""

    def test_initialization(self, mock_retriever):
        """Test agent initializes correctly."""
        with patch("app.briefings.agents.base.ChatOpenAI"):
            agent = SimilarDealsFinderAgent(retriever=mock_retriever)

        assert agent.name == "similar_deals_finder"
        assert agent.retrieval_filters.get("doc_type") == "deal"

    def test_queries_include_industry(self, mock_retriever):
        """Test that queries are built with context."""
        with patch("app.briefings.agents.base.ChatOpenAI"):
            agent = SimilarDealsFinderAgent(retriever=mock_retriever)

        queries = agent._build_queries(
            {"industry": "fintech", "company_size": "mid-market"}
        )

        assert any("fintech" in q for q in queries)


class TestCompetitorAnalystAgent:
    """Tests for CompetitorAnalystAgent."""

    def test_initialization(self, mock_retriever):
        """Test agent initializes correctly."""
        with patch("app.briefings.agents.base.ChatOpenAI"):
            agent = CompetitorAnalystAgent(retriever=mock_retriever)

        assert agent.name == "competitor_analyst"
        assert agent.retrieval_filters.get("doc_type") == "competitor"


class TestProposalDrafterAgent:
    """Tests for ProposalDrafterAgent."""

    def test_initialization(self, mock_retriever):
        """Test agent initializes correctly."""
        with patch("app.briefings.agents.base.ChatOpenAI"):
            agent = ProposalDrafterAgent(retriever=mock_retriever)

        assert agent.name == "proposal_drafter"

    def test_custom_query_building(self, mock_retriever):
        """Test that ProposalDrafterAgent builds queries with fallbacks."""
        with patch("app.briefings.agents.base.ChatOpenAI"):
            agent = ProposalDrafterAgent(retriever=mock_retriever)

        # With context
        queries = agent._build_queries(
            {"company_size": "enterprise", "industry": "healthcare"}
        )
        assert any("enterprise" in q for q in queries)

        # Without context (should use defaults)
        queries = agent._build_queries({})
        assert any("mid-market" in q for q in queries)


# =============================================================================
# Orchestrator Tests
# =============================================================================


class TestOrchestratorAgent:
    """Tests for OrchestratorAgent."""

    def test_initialization(self, mock_retriever):
        """Test orchestrator initializes with all specialists."""
        with patch("app.briefings.agents.base.ChatOpenAI"):
            orchestrator = OrchestratorAgent(retriever=mock_retriever)

        assert orchestrator.name == "orchestrator"
        assert len(orchestrator.specialists) == 4
        assert "company_researcher" in orchestrator.specialists
        assert "similar_deals_finder" in orchestrator.specialists
        assert "competitor_analyst" in orchestrator.specialists
        assert "proposal_drafter" in orchestrator.specialists

    def test_generate_briefing_returns_response(
        self, mock_retriever, mock_llm_response
    ):
        """Test that generate_briefing returns a BriefingResponse."""
        with patch("app.briefings.agents.base.ChatOpenAI") as mock_chat:
            mock_chat.return_value.invoke.return_value = mock_llm_response
            orchestrator = OrchestratorAgent(retriever=mock_retriever)

            # Mock all specialist LLMs
            for specialist in orchestrator.specialists.values():
                specialist.llm.invoke = MagicMock(return_value=mock_llm_response)

            request = BriefingRequest(
                company_name="Acme Corp",
                industry="healthcare",
                company_size="mid-market",
            )

            briefing = orchestrator.generate_briefing(request)

        assert briefing is not None
        assert briefing.metadata is not None
        assert len(briefing.metadata.agents_used) > 0

    def test_handles_specialist_failure(self, mock_retriever, mock_llm_response):
        """Test that orchestrator handles specialist failures gracefully."""
        with patch("app.briefings.agents.base.ChatOpenAI") as mock_chat:
            mock_chat.return_value.invoke.return_value = mock_llm_response
            orchestrator = OrchestratorAgent(retriever=mock_retriever)

            # Make one specialist fail
            orchestrator.specialists["company_researcher"].execute = MagicMock(
                side_effect=Exception("Test failure")
            )

            # Mock other specialists
            for name, specialist in orchestrator.specialists.items():
                if name != "company_researcher":
                    specialist.llm.invoke = MagicMock(return_value=mock_llm_response)

            request = BriefingRequest(
                company_name="Acme Corp",
                industry="healthcare",
            )

            # Should not raise, should return partial briefing
            briefing = orchestrator.generate_briefing(request)

        assert briefing is not None
        # Confidence should be reduced due to failure
        assert briefing.metadata.confidence_score < 1.0

    def test_tracks_all_sources(self, mock_retriever, mock_llm_response):
        """Test that orchestrator tracks sources from all specialists."""
        with patch("app.briefings.agents.base.ChatOpenAI") as mock_chat:
            mock_chat.return_value.invoke.return_value = mock_llm_response
            orchestrator = OrchestratorAgent(retriever=mock_retriever)

            for specialist in orchestrator.specialists.values():
                specialist.llm.invoke = MagicMock(return_value=mock_llm_response)

            request = BriefingRequest(
                company_name="Acme Corp",
                industry="healthcare",
            )

            briefing = orchestrator.generate_briefing(request)

        # Should have cited some documents
        assert briefing.metadata is not None
        assert briefing.metadata.documents_searched > 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestBriefingIntegration:
    """Integration tests for the briefing system."""

    def test_end_to_end_flow(self, mock_retriever, mock_llm_response):
        """Test the full briefing generation flow."""
        with patch("app.briefings.agents.base.ChatOpenAI") as mock_chat:
            mock_chat.return_value.invoke.return_value = mock_llm_response

            orchestrator = OrchestratorAgent(retriever=mock_retriever)

            for specialist in orchestrator.specialists.values():
                specialist.llm.invoke = MagicMock(return_value=mock_llm_response)

            request = BriefingRequest(
                company_name="TechCorp",
                industry="fintech",
                company_size="enterprise",
                meeting_type="demo",
                specific_questions=["How do we compare to competitors?"],
            )

            briefing = orchestrator.generate_briefing(request)

        # Verify structure
        assert "company_summary" in briefing.model_dump() or briefing.company_summary
        assert briefing.metadata is not None
        assert briefing.metadata.generated_at is not None
        assert len(briefing.metadata.agents_used) >= 0
