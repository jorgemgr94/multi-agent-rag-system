"""Briefing service - business logic for briefing generation."""

from app.briefings.agents import OrchestratorAgent
from app.briefings.schemas import BriefingRequest, BriefingResponse
from app.core import get_logger
from app.documents.agents import RetrieverAgent
from app.documents.memory import get_vector_store

logger = get_logger(__name__)


class BriefingService:
    """Service layer for briefing generation.

    Encapsulates the orchestration logic and provides
    a clean interface for the API layer.
    """

    def __init__(self):
        """Initialize the briefing service."""
        # Get vector store (singleton)
        vector_store = get_vector_store()

        # Initialize retriever
        self.retriever = RetrieverAgent(vector_store=vector_store)

        # Initialize orchestrator
        self.orchestrator = OrchestratorAgent(retriever=self.retriever)

        logger.info("BriefingService initialized")

    def generate_briefing(self, request: BriefingRequest) -> BriefingResponse:
        """Generate a deal briefing.

        Args:
            request: Briefing request with company details

        Returns:
            Complete briefing response
        """
        logger.info(f"Generating briefing for: {request.company_name}")

        # Delegate to orchestrator
        briefing = self.orchestrator.generate_briefing(request)

        docs_cited = briefing.metadata.documents_cited if briefing.metadata else 0
        logger.info(f"Briefing generated: {docs_cited} sources cited")

        return briefing


# Singleton instance
_service: BriefingService | None = None


def get_briefing_service() -> BriefingService:
    """Get or create the briefing service singleton."""
    global _service
    if _service is None:
        _service = BriefingService()
    return _service
