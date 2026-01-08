"""Document and retrieval schemas."""

import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Document Type Enums
# =============================================================================


class DocType(str, Enum):
    """Types of documents in the knowledge base."""

    DEAL = "deal"
    PROPOSAL = "proposal"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    CASE_STUDY = "case_study"
    INDUSTRY = "industry"
    RECORDING = "recording"  # For voice/call transcripts


class CompanySize(str, Enum):
    """Company size categories."""

    STARTUP = "startup"
    MID_MARKET = "mid-market"
    ENTERPRISE = "enterprise"


class DealOutcome(str, Enum):
    """Deal outcome status."""

    WON = "won"
    LOST = "lost"
    PENDING = "pending"


# =============================================================================
# Document Schemas
# =============================================================================


class DocumentMetadata(BaseModel):
    """Metadata schema for documents.

    Used for filtering and hybrid search.
    """

    doc_id: str = Field(..., description="Unique document identifier")
    doc_type: DocType = Field(..., description="Type of document")
    industry: str | None = Field(default=None, description="Industry vertical")
    company_size: CompanySize | None = Field(default=None)
    deal_value: int | None = Field(default=None, description="Deal value in USD")
    outcome: DealOutcome | None = Field(default=None, description="Deal outcome")
    date: datetime.date | None = Field(default=None, description="Document date")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    source_file: str = Field(..., description="Original file path")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for vector store metadata."""
        data = self.model_dump(mode="json")
        # Convert enums to strings for FAISS metadata
        if self.doc_type:
            data["doc_type"] = self.doc_type.value
        if self.company_size:
            data["company_size"] = self.company_size.value
        if self.outcome:
            data["outcome"] = self.outcome.value
        return data


class Document(BaseModel):
    """A document to be ingested into the vector store."""

    content: str = Field(..., description="Full document content")
    metadata: DocumentMetadata


class Chunk(BaseModel):
    """A chunk of a document after splitting."""

    content: str = Field(..., description="Chunk text content")
    metadata: DocumentMetadata
    chunk_index: int = Field(..., description="Index of chunk within document")
    total_chunks: int = Field(..., description="Total chunks in parent document")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for vector store."""
        data = self.metadata.to_dict()
        data["chunk_index"] = self.chunk_index
        data["total_chunks"] = self.total_chunks
        return data


# =============================================================================
# Search Schemas
# =============================================================================


class SearchResult(BaseModel):
    """A single search result from the vector store."""

    content: str = Field(..., description="Chunk content")
    score: float = Field(..., description="Similarity score (0-1)")
    metadata: dict[str, Any] = Field(..., description="Document metadata")

    @property
    def doc_id(self) -> str:
        return self.metadata.get("doc_id", "unknown")

    @property
    def doc_type(self) -> str:
        return self.metadata.get("doc_type", "unknown")

    @property
    def source_file(self) -> str:
        return self.metadata.get("source_file", "unknown")


class SearchQuery(BaseModel):
    """Query for semantic search."""

    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Metadata filters (e.g., {'doc_type': 'deal', 'industry': 'healthcare'})",
    )


class SearchResponse(BaseModel):
    """Response from semantic search."""

    results: list[SearchResult]
    total_searched: int = Field(..., description="Total documents in index")
    query: str


# =============================================================================
# Retrieval Schemas
# =============================================================================


class RetrievalResult(BaseModel):
    """A single retrieval result with source tracking."""

    content: str = Field(..., description="Retrieved text content")
    score: float = Field(..., description="Similarity score (0-1)")
    doc_id: str = Field(..., description="Source document ID")
    doc_type: str = Field(..., description="Type of document")
    source_file: str = Field(..., description="Original file path")
    chunk_index: int = Field(default=0, description="Chunk index in document")

    @classmethod
    def from_search_result(cls, result: SearchResult) -> "RetrievalResult":
        """Create from a SearchResult."""
        return cls(
            content=result.content,
            score=result.score,
            doc_id=result.doc_id,
            doc_type=result.doc_type,
            source_file=result.source_file,
            chunk_index=result.metadata.get("chunk_index", 0),
        )


class RetrievalObservation(BaseModel):
    """Structured observation from retrieval."""

    query: str = Field(..., description="Original query")
    rewritten_query: str = Field(..., description="Optimized search query")
    results: list[RetrievalResult] = Field(default_factory=list)
    total_results: int = Field(default=0)
    total_tokens: int = Field(default=0, description="Tokens in retrieved content")
    filters_applied: dict | None = Field(default=None)
