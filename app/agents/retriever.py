"""Retriever Agent for RAG-based knowledge retrieval."""

import tiktoken
from langchain_openai import ChatOpenAI

from app.agents.base import BaseAgent
from app.config import settings
from app.logging_config import get_logger
from app.memory.base import VectorStoreRepository
from app.schemas.document import SearchQuery, SearchResult
from app.schemas.retrieval import RetrievalObservation, RetrievalResult
from app.schemas.task import (
    AgentDecision,
    DecisionType,
    Observation,
    TaskInput,
    ToolCall,
)

logger = get_logger(__name__)


# =============================================================================
# Retrieval Configuration
# =============================================================================

# Context window limits (in tokens)
MAX_CONTEXT_TOKENS = 4000  # Leave room for system prompt + response
MIN_RELEVANCE_SCORE = 0.5  # Minimum similarity score to include

# Top-k configuration
DEFAULT_TOP_K = 5
MAX_TOP_K = 10
MIN_TOP_K = 1


# =============================================================================
# Query Rewriting Prompts
# =============================================================================

QUERY_REWRITE_SYSTEM = """You are a search query optimizer for a sales knowledge base.

Your job is to rewrite queries to maximize retrieval quality from a vector database.

The knowledge base contains:
- Past deal records (company, industry, outcome, learnings)
- Competitor analyses
- Product documentation and pricing
- Industry playbooks
- Case studies and proposals

Rules:
1. Expand abbreviations and jargon
2. Add relevant synonyms
3. Make implicit context explicit
4. Keep the rewritten query concise (1-2 sentences max)
5. Focus on searchable concepts, not questions

Output ONLY the rewritten query, nothing else."""

QUERY_REWRITE_USER = """Original query: {query}
Context: {context}

Rewritten query:"""


class RetrieverAgent(BaseAgent):
    """Agent responsible for knowledge retrieval via RAG.

    Responsibilities:
    - Rewrite queries for better search quality
    - Search vector store with appropriate filters
    - Manage context window limits
    - Return traceable, structured results

    Design principles:
    - Retrieval is intentional, not automatic
    - More context is not always better
    - All results must be traceable to sources
    """

    name: str = "retriever"
    description: str = "Retrieves relevant knowledge from the vector database"

    def __init__(
        self,
        vector_store: VectorStoreRepository,
        model: str | None = None,
        max_context_tokens: int = MAX_CONTEXT_TOKENS,
    ):
        """Initialize the retriever agent.

        Args:
            vector_store: Vector store to search
            model: LLM model for query rewriting
            max_context_tokens: Maximum tokens to include in context
        """
        self.vector_store = vector_store
        self.max_context_tokens = max_context_tokens

        # LLM for query rewriting
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=model or settings.openai_model,
            temperature=0,  # Deterministic rewrites
        )

        # Tokenizer for context management
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def reason(
        self,
        task_input: TaskInput,
        observations: list[Observation] | None = None,
    ) -> AgentDecision:
        """Process a retrieval request.

        The retriever agent always returns a RETRIEVE decision with
        the retrieval results as a tool call.

        Args:
            task_input: Contains the query and optional context/filters
            observations: Previous observations (not typically used)

        Returns:
            AgentDecision with retrieval results
        """
        query = task_input.task
        context = task_input.context or {}

        # Extract filters from context if provided
        filters = context.get("filters")
        top_k = context.get("top_k", DEFAULT_TOP_K)

        # Perform retrieval
        observation = self.retrieve(query, filters=filters, top_k=top_k)

        # Return as a structured decision
        return AgentDecision(
            decision_type=DecisionType.RETRIEVE,
            reasoning=(
                f"Retrieved {observation.total_results} results "
                f"for query: {observation.rewritten_query}"
            ),
            tool_call=ToolCall(
                tool_name="vector_search",
                arguments={
                    "query": observation.rewritten_query,
                    "top_k": top_k,
                    "filters": filters,
                },
            ),
            message=None,
        )

    def retrieve(
        self,
        query: str,
        filters: dict | None = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> RetrievalObservation:
        """Perform retrieval with query rewriting and context management.

        Args:
            query: User's search query
            filters: Optional metadata filters
            top_k: Maximum number of results

        Returns:
            Structured retrieval observation
        """
        # Clamp top_k to valid range
        top_k = max(MIN_TOP_K, min(MAX_TOP_K, top_k))

        # Step 1: Rewrite query for better retrieval
        rewritten_query = self._rewrite_query(query, filters)
        logger.info(f"Query rewritten: '{query}' -> '{rewritten_query}'")

        # Step 2: Search vector store
        search_query = SearchQuery(
            query=rewritten_query,
            top_k=top_k,
            filters=filters,
        )
        search_response = self.vector_store.search(search_query)

        # Step 3: Filter by minimum relevance score
        relevant_results = [
            r for r in search_response.results if r.score >= MIN_RELEVANCE_SCORE
        ]

        # Step 4: Apply context window limits
        selected_results = self._select_within_token_limit(relevant_results)

        # Step 5: Convert to retrieval results with source tracking
        retrieval_results = [
            RetrievalResult.from_search_result(r) for r in selected_results
        ]

        # Calculate total tokens in retrieved content
        total_tokens = sum(self.count_tokens(r.content) for r in retrieval_results)

        logger.info(
            f"Retrieval complete: {len(retrieval_results)} results, "
            f"{total_tokens} tokens"
        )

        return RetrievalObservation(
            query=query,
            rewritten_query=rewritten_query,
            results=retrieval_results,
            total_results=len(retrieval_results),
            total_tokens=total_tokens,
            filters_applied=filters,
        )

    def _rewrite_query(self, query: str, context: dict | None = None) -> str:
        """Rewrite a query for better vector search.

        Uses LLM to expand and optimize the query for semantic search.

        Args:
            query: Original user query
            context: Optional context (filters, etc.)

        Returns:
            Rewritten query optimized for retrieval
        """
        # Skip rewriting for very short queries or if it looks like
        # it's already a well-formed search query
        if len(query.split()) <= 2:
            return query

        try:
            context_str = str(context) if context else "None"
            user_prompt = QUERY_REWRITE_USER.format(query=query, context=context_str)

            response = self.llm.invoke(
                [
                    {"role": "system", "content": QUERY_REWRITE_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ]
            )

            content = response.content
            rewritten = content.strip() if isinstance(content, str) else query

            # Sanity check: rewritten query shouldn't be empty or too long
            if not rewritten or len(rewritten) > 500:
                return query

            return rewritten

        except Exception as e:
            logger.warning(f"Query rewrite failed, using original: {e}")
            return query

    def _select_within_token_limit(
        self, results: list[SearchResult]
    ) -> list[SearchResult]:
        """Select results that fit within the context token limit.

        Prioritizes higher-scoring results.

        Args:
            results: Sorted search results (by score, descending)

        Returns:
            Subset of results that fit within token limit
        """
        selected = []
        current_tokens = 0

        for result in results:
            result_tokens = self.count_tokens(result.content)

            if current_tokens + result_tokens > self.max_context_tokens:
                # Would exceed limit - stop here
                logger.debug(
                    f"Token limit reached: {current_tokens}/{self.max_context_tokens}, "
                    f"stopping after {len(selected)} results"
                )
                break

            selected.append(result)
            current_tokens += result_tokens

        return selected

    def to_observation(self, retrieval: RetrievalObservation) -> Observation:
        """Convert retrieval results to a standard Observation.

        Args:
            retrieval: Retrieval observation

        Returns:
            Standard Observation for agent communication
        """
        return Observation(
            source="retrieval",
            success=True,
            result={
                "query": retrieval.query,
                "rewritten_query": retrieval.rewritten_query,
                "total_results": retrieval.total_results,
                "total_tokens": retrieval.total_tokens,
                "results": [r.model_dump() for r in retrieval.results],
            },
        )

    def format_context(self, retrieval: RetrievalObservation) -> str:
        """Format retrieval results as context for another agent.

        Creates a structured context string suitable for injection
        into an LLM prompt.

        Args:
            retrieval: Retrieval observation

        Returns:
            Formatted context string with source citations
        """
        if not retrieval.results:
            return "No relevant documents found."

        sections = []
        for i, result in enumerate(retrieval.results, 1):
            section = f"""[Source {i}: {result.source_file}]
Type: {result.doc_type}
Relevance: {result.score:.2f}
---
{result.content}
---"""
            sections.append(section)

        header = f"Retrieved {len(retrieval.results)} relevant documents:\n"
        return header + "\n\n".join(sections)
