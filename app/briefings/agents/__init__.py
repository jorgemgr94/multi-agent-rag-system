"""Briefing agents module.

Contains:
- OrchestratorAgent: Coordinates workflow, synthesizes final briefing
- CompanyResearcherAgent: Finds industry insights, market context
- SimilarDealsFinderAgent: Identifies past deals with similar characteristics
- CompetitorAnalystAgent: Retrieves competitive positioning
- ProposalDrafterAgent: Generates customized talking points
"""

from app.briefings.agents.base import SpecialistAgent, SpecialistResult
from app.briefings.agents.orchestrator import OrchestrationState, OrchestratorAgent
from app.briefings.agents.specialists import (
    CompanyResearcherAgent,
    CompetitorAnalystAgent,
    ProposalDrafterAgent,
    SimilarDealsFinderAgent,
)

__all__ = [
    # Orchestrator
    "OrchestratorAgent",
    "OrchestrationState",
    # Base
    "SpecialistAgent",
    "SpecialistResult",
    # Specialists
    "CompanyResearcherAgent",
    "SimilarDealsFinderAgent",
    "CompetitorAnalystAgent",
    "ProposalDrafterAgent",
]
