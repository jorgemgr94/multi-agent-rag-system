"""Documents feature module.

Handles document ingestion, storage, retrieval, and search.
"""

from app.documents.ingestion import DocumentChunker, DocumentLoader, IngestionPipeline
from app.documents.memory import vector_store
from app.documents.retriever import RetrieverAgent
from app.documents.schemas import (
    Chunk,
    CompanySize,
    DealOutcome,
    DocType,
    Document,
    DocumentMetadata,
    RetrievalObservation,
    RetrievalResult,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

__all__ = [
    # Ingestion
    "DocumentChunker",
    "DocumentLoader",
    "IngestionPipeline",
    # Memory
    "vector_store",
    # Retriever
    "RetrieverAgent",
    # Schemas
    "Chunk",
    "CompanySize",
    "DealOutcome",
    "DocType",
    "Document",
    "DocumentMetadata",
    "RetrievalObservation",
    "RetrievalResult",
    "SearchQuery",
    "SearchResponse",
    "SearchResult",
]
