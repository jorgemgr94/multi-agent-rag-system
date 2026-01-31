"""Base class for briefing specialist agents."""

from abc import abstractmethod
import json
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core import get_logger, settings
from app.core.agents import BaseAgent
from app.core.schemas import AgentDecision, DecisionType, Observation, TaskInput
from app.documents.agents import RetrieverAgent
from app.documents.schemas import RetrievalObservation

logger = get_logger(__name__)


class SpecialistResult(BaseModel):
    """Result from a specialist agent."""

    agent_name: str = Field(..., description="Name of the specialist agent")
    success: bool = Field(default=True)
    content: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    error: str | None = None


class SpecialistAgent(BaseAgent):
    """Base class for specialist agents in the briefing system.

    Each specialist:
    1. Receives a briefing context
    2. Retrieves relevant documents via RetrieverAgent
    3. Synthesizes findings using LLM
    4. Returns structured results with sources
    """

    name: str
    description: str

    # Query templates for retrieval
    retrieval_queries: list[str] = []

    # Filters to apply to retrieval
    retrieval_filters: dict[str, Any] = {}

    def __init__(
        self,
        retriever: RetrieverAgent,
        model: str | None = None,
    ):
        """Initialize specialist agent.

        Args:
            retriever: RetrieverAgent for knowledge retrieval
            model: LLM model for synthesis
        """
        self.retriever = retriever
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=model or settings.openai_model,
            temperature=0.3,  # Slightly creative for synthesis
        )

    def reason(
        self,
        task_input: TaskInput,
        observations: list[Observation] | None = None,
    ) -> AgentDecision:
        """Process task and return decision.

        Specialists always respond with their findings.
        """
        result = self.execute(task_input.context or {})

        return AgentDecision(
            decision_type=DecisionType.RESPOND,
            reasoning=f"{self.name} completed analysis with {len(result.sources)} sources",
            message=str(result.content),
        )

    def execute(self, context: dict[str, Any]) -> SpecialistResult:
        """Execute the specialist's task.

        Args:
            context: Briefing context (company_name, industry, etc.)

        Returns:
            Structured result with findings and sources
        """
        try:
            # Step 1: Build queries from context
            queries = self._build_queries(context)

            # Step 2: Retrieve relevant documents
            retrievals = self._retrieve_all(queries, context)

            # Step 3: Synthesize findings
            content = self._synthesize(context, retrievals)

            # Step 4: Collect sources
            sources = self._collect_sources(retrievals)

            logger.info(f"{self.name}: Generated findings from {len(sources)} sources")

            return SpecialistResult(
                agent_name=self.name,
                success=True,
                content=content,
                sources=sources,
            )

        except Exception as e:
            logger.error(f"{self.name} failed: {e}")
            return SpecialistResult(
                agent_name=self.name,
                success=False,
                error=str(e),
            )

    def _build_queries(self, context: dict[str, Any]) -> list[str]:
        """Build retrieval queries from templates and context.

        Override in subclasses for custom query building.
        """
        queries = []
        for template in self.retrieval_queries:
            query = template.format(**context)
            queries.append(query)
        return queries

    def _retrieve_all(
        self, queries: list[str], context: dict[str, Any]
    ) -> list[RetrievalObservation]:
        """Execute all retrieval queries."""
        retrievals = []

        # Build filters from context and agent-specific filters
        # Note: Don't apply industry filter here - it's too restrictive
        # Let semantic search find relevant docs across industries
        filters = {**self.retrieval_filters} if self.retrieval_filters else None

        for query in queries:
            try:
                retrieval = self.retriever.retrieve(
                    query=query,
                    filters=filters if filters else None,
                    top_k=3,  # Limit per query to avoid context overflow
                )
                retrievals.append(retrieval)
            except Exception as e:
                logger.warning(f"Retrieval failed for '{query}': {e}")

        return retrievals

    def _collect_sources(self, retrievals: list[RetrievalObservation]) -> list[str]:
        """Collect unique source files from all retrievals."""
        sources = set()
        for retrieval in retrievals:
            for result in retrieval.results:
                sources.add(result.source_file)
        return list(sources)

    @abstractmethod
    def _synthesize(
        self, context: dict[str, Any], retrievals: list[RetrievalObservation]
    ) -> dict[str, Any]:
        """Synthesize findings from retrieved documents.

        Must be implemented by each specialist.

        Args:
            context: Briefing context
            retrievals: Retrieved documents

        Returns:
            Structured findings
        """
        pass

    def _format_retrieval_context(self, retrievals: list[RetrievalObservation]) -> str:
        """Format all retrievals as context for LLM."""
        if not retrievals:
            return "No relevant documents found."

        sections = []
        doc_num = 1

        for retrieval in retrievals:
            for result in retrieval.results:
                section = f"""[Document {doc_num}: {result.source_file}]
{result.content}
---"""
                sections.append(section)
                doc_num += 1

        return "\n\n".join(sections)

    def _parse_json_response(self, content: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling code blocks."""
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())
