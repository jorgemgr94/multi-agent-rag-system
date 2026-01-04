"""FastAPI application for the multi-agent RAG system."""

from fastapi import FastAPI

from app.config import settings
from app.logging_config import get_logger, setup_logging
from app.schemas.task import ResponseStatus, TaskRequest, TaskResponse

# Initialize logging from config
setup_logging(level=settings.log_level, structured=settings.log_structured)
logger = get_logger(__name__)

app = FastAPI(
    title="Multi-Agent RAG System",
    description="Multi-agent system with RAG, vector databases, and semantic memory",
    version="0.1.0",
)


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
        "agents": {
            "available": [],
            "count": 0,
        },
    }


@app.post("/tasks", response_model=TaskResponse)
def run_task(payload: TaskRequest):
    """Process a task through the multi-agent system."""
    logger.info(f"Received task: {payload.task[:50]}...")
    # Placeholder until orchestrator is implemented
    return TaskResponse(
        status=ResponseStatus.FAILED,
        message="Multi-agent orchestrator not implemented yet",
        data={"received_task": payload.task},
    )
