"""Document and chunk schemas for the vector database."""

import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocType(str, Enum):
    """Types of documents in the knowledge base."""

    DEAL = "deal"
    PROPOSAL = "proposal"
    COMPETITOR = "competitor"
    PRODUCT = "product"
    CASE_STUDY = "case_study"
    INDUSTRY = "industry"


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
