"""FastAPI application for the Deal Intelligence Platform."""

from fastapi import FastAPI

from app.briefings.router import router as briefings_router
from app.core import get_logger, settings, setup_logging
from app.documents.memory import vector_store
from app.documents.router import router as documents_router

# Initialize logging from config
setup_logging(level=settings.log_level, structured=settings.log_structured)
logger = get_logger(__name__)

app = FastAPI(
    title="Deal Intelligence Platform",
    description="Multi-agent RAG system for sales deal preparation",
    version="0.2.0",
)

# =============================================================================
# Feature Routers
# =============================================================================

app.include_router(documents_router, prefix="/documents", tags=["Documents"])
app.include_router(briefings_router, prefix="/briefings", tags=["Briefings"])


# =============================================================================
# Health & Status Endpoints
# =============================================================================


@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@app.get("/status")
def status():
    """Detailed status endpoint."""
    return {
        "status": "ok",
        "config": {
            "model": settings.openai_model,
        },
        "vector_store": {
            "document_count": vector_store.count,
        },
        "features": {
            "documents": "active",
            "briefings": "placeholder",
            "calls": "not_implemented",
        },
    }
