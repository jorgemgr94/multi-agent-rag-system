"""FastAPI router for document endpoints."""

from fastapi import APIRouter, HTTPException

from app.core import INDEX_PATH, KNOWLEDGE_BASE_PATH, get_logger
from app.documents.ingestion import IngestionPipeline
from app.documents.memory import vector_store
from app.documents.schemas import SearchQuery, SearchResponse

logger = get_logger(__name__)

router = APIRouter()


@router.post("/ingest")
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


@router.get("")
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


@router.post("/search", response_model=SearchResponse)
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
