"""Orchestrator Agent for coordinating briefing generation."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.briefings.agents.base import SpecialistAgent, SpecialistResult
from app.briefings.agents.specialists import (
    CompanyResearcherAgent,
    CompetitorAnalystAgent,
    ProposalDrafterAgent,
    SimilarDealsFinderAgent,
)
from app.briefings.schemas import (
    BriefingMetadata,
    BriefingRequest,
    BriefingResponse,
    CompetitivePositioning,
    RecommendedApproach,
    SimilarDeal,
)
from app.core import get_logger
from app.core.schemas import AgentDecision, DecisionType, Observation, TaskInput
from app.documents.agents import RetrieverAgent

logger = get_logger(__name__)


# =============================================================================
# Orchestration State
# =============================================================================


class OrchestrationState(BaseModel):
    """State tracking for orchestration."""

    request: BriefingRequest
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_agents: list[str] = Field(default_factory=list)
    failed_agents: list[str] = Field(default_factory=list)
    results: dict[str, SpecialistResult] = Field(default_factory=dict)
    total_sources: set[str] = Field(default_factory=set)

    model_config = {"arbitrary_types_allowed": True}


# =============================================================================
# Orchestrator Agent
# =============================================================================


class OrchestratorAgent():
    """Coordinates specialist agents to generate deal briefings.

    Responsibilities:
    - Initialize and manage specialist agents
    - Execute specialists in appropriate order
    - Handle failures gracefully (partial results)
    - Synthesize final briefing from all results
    - Track sources and metadata

    Design principles:
    - Fail gracefully: partial briefings > no briefing
    - Log everything: decisions, transitions, timings
    - Deterministic: same input → same output
    """

    name: str = "orchestrator"
    description: str = "Coordinates specialists to generate deal briefings"

    def __init__(self, retriever: RetrieverAgent, model: str | None = None):
        """Initialize orchestrator with specialists.

        Args:
            retriever: Shared retriever for all specialists
            model: LLM model for specialists
        """
        self.retriever = retriever

        # Initialize specialist agents
        self.specialists: dict[str, SpecialistAgent] = {
            "company_researcher": CompanyResearcherAgent(retriever, model),
            "similar_deals_finder": SimilarDealsFinderAgent(retriever, model),
            "competitor_analyst": CompetitorAnalystAgent(retriever, model),
            "proposal_drafter": ProposalDrafterAgent(retriever, model),
        }

        logger.info(
            f"Orchestrator initialized with {len(self.specialists)} specialists"
        )

    def reason(
        self,
        task_input: TaskInput,
        observations: list[Observation] | None = None,
    ) -> AgentDecision:
        """Process a briefing request.

        The orchestrator always returns a RESPOND decision with
        the synthesized briefing.
        """
        # Build request from task context
        context = task_input.context or {}
        request = BriefingRequest(
            company_name=context.get("company_name", task_input.task),
            industry=context.get("industry"),
            company_size=context.get("company_size"),
            meeting_type=context.get("meeting_type"),
            specific_questions=context.get("specific_questions", []),
        )

        # Generate briefing
        briefing = self.generate_briefing(request)

        agents_count = len(briefing.metadata.agents_used) if briefing.metadata else 0

        return AgentDecision(
            decision_type=DecisionType.RESPOND,
            reasoning=f"Generated briefing using {agents_count} agents",
            message=briefing.model_dump_json(),
        )

    def generate_briefing(self, request: BriefingRequest) -> BriefingResponse:
        """Generate a complete deal briefing.

        Args:
            request: Briefing request with company details

        Returns:
            Complete briefing response
        """
        logger.info(f"Starting briefing generation for: {request.company_name}")

        # Initialize state
        state = OrchestrationState(request=request)

        # Build context for specialists
        context = self._build_context(request)

        # Execute specialists (order matters for some use cases)
        execution_order = [
            "company_researcher",  # Industry context first
            "similar_deals_finder",  # Then historical precedents
            "competitor_analyst",  # Competitive landscape
            "proposal_drafter",  # Finally, recommendations
        ]

        for agent_name in execution_order:
            self._execute_specialist(agent_name, context, state)

        # Synthesize final briefing
        briefing = self._synthesize_briefing(state)

        logger.info(
            f"Briefing complete: {len(state.completed_agents)} succeeded, "
            f"{len(state.failed_agents)} failed, "
            f"{len(state.total_sources)} sources"
        )

        return briefing

    def _build_context(self, request: BriefingRequest) -> dict[str, Any]:
        """Build context dictionary from request."""
        return {
            "company_name": request.company_name,
            "industry": request.industry or "general",
            "company_size": request.company_size or "mid-market",
            "meeting_type": request.meeting_type or "initial_call",
            "specific_questions": request.specific_questions,
        }

    def _execute_specialist(
        self,
        agent_name: str,
        context: dict[str, Any],
        state: OrchestrationState,
    ) -> None:
        """Execute a single specialist agent.

        Args:
            agent_name: Name of the specialist to execute
            context: Briefing context
            state: Current orchestration state
        """
        specialist = self.specialists.get(agent_name)
        if not specialist:
            logger.warning(f"Unknown specialist: {agent_name}")
            return

        logger.info(f"Executing specialist: {agent_name}")

        try:
            result = specialist.execute(context)
            state.results[agent_name] = result

            if result.success:
                state.completed_agents.append(agent_name)
                state.total_sources.update(result.sources)
                logger.info(
                    f"{agent_name} succeeded with {len(result.sources)} sources"
                )
            else:
                state.failed_agents.append(agent_name)
                logger.warning(f"{agent_name} failed: {result.error}")

        except Exception as e:
            logger.error(f"{agent_name} raised exception: {e}")
            state.failed_agents.append(agent_name)
            state.results[agent_name] = SpecialistResult(
                agent_name=agent_name,
                success=False,
                error=str(e),
            )

    def _synthesize_briefing(self, state: OrchestrationState) -> BriefingResponse:
        """Synthesize final briefing from all specialist results."""
        # Extract results
        company_result = state.results.get("company_researcher")
        deals_result = state.results.get("similar_deals_finder")
        competitor_result = state.results.get("competitor_analyst")
        proposal_result = state.results.get("proposal_drafter")

        # Build company summary
        company_summary = {}
        if company_result and company_result.success:
            company_summary = {
                "overview": company_result.content.get("overview", ""),
                "industry_context": {
                    "priorities": company_result.content.get("key_priorities", []),
                    "trends": company_result.content.get("relevant_trends", []),
                },
                "considerations": company_result.content.get("considerations", []),
                "sources": company_result.sources,
            }

        # Build similar deals
        similar_deals = []
        if deals_result and deals_result.success:
            for deal in deals_result.content.get("similar_deals", []):
                similar_deals.append(
                    SimilarDeal(
                        company=deal.get("company", "Unknown"),
                        similarity_score=0.85,  # Could be computed
                        outcome=deal.get("outcome", "unknown"),
                        deal_value=deal.get("deal_value"),
                        key_learnings=deal.get("similarity_reason", ""),
                        source=deals_result.sources[0] if deals_result.sources else "",
                    )
                )

        # Build competitive positioning
        competitive_positioning = None
        if competitor_result and competitor_result.success:
            objections = []
            for obj in competitor_result.content.get("objection_responses", []):
                if isinstance(obj, dict):
                    objections.append(
                        f"{obj.get('objection', '')}: {obj.get('response', '')}"
                    )
                else:
                    objections.append(str(obj))

            competitive_positioning = CompetitivePositioning(
                summary=competitor_result.content.get("positioning_strategy", ""),
                objection_responses=objections,
                sources=competitor_result.sources,
            )

        # Build recommended approach
        recommended_approach = None
        if proposal_result and proposal_result.success:
            recommended_approach = RecommendedApproach(
                talking_points=proposal_result.content.get("talking_points", []),
                questions_to_ask=proposal_result.content.get("discovery_questions", []),
                pricing_guidance=proposal_result.content.get("pricing_guidance"),
                sources=proposal_result.sources,
            )

        # Build metadata
        metadata = BriefingMetadata(
            generated_at=datetime.now(timezone.utc).isoformat(),
            documents_searched=self.retriever.vector_store.count,
            documents_cited=len(state.total_sources),
            confidence_score=self._calculate_confidence(state),
            agents_used=state.completed_agents,
        )

        return BriefingResponse(
            company_summary=company_summary,
            similar_deals=similar_deals,
            competitive_positioning=competitive_positioning,
            recommended_approach=recommended_approach,
            metadata=metadata,
        )

    def _calculate_confidence(self, state: OrchestrationState) -> float:
        """Calculate confidence score based on agent success rate."""
        total = len(self.specialists)
        succeeded = len(state.completed_agents)

        if total == 0:
            return 0.0

        # Base score from success rate
        base_score = succeeded / total

        # Bonus for having sources
        source_bonus = min(0.1, len(state.total_sources) * 0.02)

        return min(1.0, base_score + source_bonus)
