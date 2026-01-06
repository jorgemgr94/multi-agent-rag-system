"""FastAPI application for the multi-agent RAG system."""

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.ingestion import IngestionPipeline
from app.logging_config import get_logger, setup_logging
from app.memory import INDEX_PATH, KNOWLEDGE_BASE_PATH, vector_store
from app.schemas.document import SearchQuery, SearchResponse
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
        "vector_store": {
            "document_count": vector_store.count,
            "index_path": str(INDEX_PATH),
        },
        "agents": {
            "available": [],
            "count": 0,
        },
    }


# =============================================================================
# Document & Search Endpoints
# =============================================================================


@app.post("/documents/ingest")
def ingest_documents():
    """Ingest documents from the knowledge base into the vector store."""
    vector_store.clear()

    # Run ingestion pipeline
    pipeline = IngestionPipeline(KNOWLEDGE_BASE_PATH)
    chunks = pipeline.run()

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail=f"No documents found in {KNOWLEDGE_BASE_PATH}",
        )

    # Add chunks to vector store
    added = vector_store.add_chunks(chunks)
    vector_store.save(INDEX_PATH)

    logger.info(f"Ingested {added} chunks from {KNOWLEDGE_BASE_PATH}")

    return {
        "status": "success",
        "chunks_ingested": added,
        "index_path": str(INDEX_PATH),
    }


@app.get("/documents")
def list_documents():
    """List indexed documents with metadata."""
    if vector_store.count == 0:
        return {
            "status": "empty",
            "message": "No documents indexed. Run POST /documents/ingest first.",
            "documents": [],
        }

    # Get unique documents from metadata
    seen_docs = {}
    for meta in vector_store.get_all_metadata():
        doc_id = meta.get("doc_id")
        if doc_id and doc_id not in seen_docs:
            seen_docs[doc_id] = {
                "doc_id": doc_id,
                "doc_type": meta.get("doc_type"),
                "source_file": meta.get("source_file"),
                "industry": meta.get("industry"),
            }

    return {
        "status": "ok",
        "total_chunks": vector_store.count,
        "documents": list(seen_docs.values()),
    }


@app.post("/documents/search", response_model=SearchResponse)
def search_documents(query: SearchQuery):
    """Semantic search across the knowledge base."""
    if vector_store.count == 0:
        raise HTTPException(
            status_code=400,
            detail="Vector store is empty. Run POST /documents/ingest first.",
        )

    logger.info(
        f"Search: '{query.query}' (top_k={query.top_k}, filters={query.filters})"
    )

    return vector_store.search(query)


# =============================================================================
# Task/Briefing Endpoints (Placeholder for M4)
# =============================================================================


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


@app.post("/briefings")
def generate_briefing(
    company_name: str,
    industry: str | None = None,
    company_size: str | None = None,
    meeting_type: str | None = None,
):
    """Generate a deal briefing (placeholder for M4)."""
    return {
        "status": "not_implemented",
        "message": "Briefing generation requires multi-agent orchestration (M4)",
        "input": {
            "company_name": company_name,
            "industry": industry,
            "company_size": company_size,
            "meeting_type": meeting_type,
        },
    }
