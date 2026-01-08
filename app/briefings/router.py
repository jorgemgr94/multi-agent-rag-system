"""FastAPI router for briefing endpoints."""

from fastapi import APIRouter

from app.briefings.schemas import BriefingRequest
from app.core import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("")
def generate_briefing(request: BriefingRequest):
    """Generate a deal briefing.

    This endpoint will be fully implemented in M4 with multi-agent orchestration.
    """
    logger.info(f"Briefing requested for: {request.company_name}")

    return {
        "status": "not_implemented",
        "message": "Briefing generation requires multi-agent orchestration (M4)",
        "input": request.model_dump(),
    }
