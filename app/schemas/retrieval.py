"""Retrieval-related schemas for the retriever agent."""

from pydantic import BaseModel, Field

from app.schemas.document import SearchResult


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
