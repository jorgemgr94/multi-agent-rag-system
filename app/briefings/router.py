"""FastAPI router for briefing endpoints."""

from fastapi import APIRouter, HTTPException

from app.briefings.schemas import BriefingRequest, BriefingResponse
from app.briefings.service import get_briefing_service
from app.core import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=BriefingResponse)
def generate_briefing(request: BriefingRequest) -> BriefingResponse:
    """Generate a deal briefing.

    Coordinates multiple specialist agents to produce a comprehensive
    briefing including:
    - Company/industry context
    - Similar past deals
    - Competitive positioning
    - Recommended approach and talking points

    Args:
        request: Briefing request with company details

    Returns:
        Complete deal briefing
    """
    logger.info(f"Briefing requested for: {request.company_name}")

    try:
        service = get_briefing_service()
        briefing = service.generate_briefing(request)
        return briefing

    except Exception as e:
        logger.error(f"Briefing generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Briefing generation failed: {str(e)}",
        )


@router.get("/health")
def briefing_health():
    """Health check for briefing service."""
    try:
        service = get_briefing_service()
        return {
            "status": "healthy",
            "vector_store_count": service.retriever.vector_store.count,
            "specialists": list(service.orchestrator.specialists.keys()),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
