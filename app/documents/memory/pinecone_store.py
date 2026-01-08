"""Pinecone vector store implementation."""

from pathlib import Path
from typing import Any

from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone

from app.core import get_logger, settings
from app.documents.memory.base import VectorStoreRepository
from app.documents.schemas import Chunk, SearchQuery, SearchResponse, SearchResult

logger = get_logger(__name__)


class PineconeVectorStore(VectorStoreRepository):
    """Pinecone-based vector store implementation.

    Managed vector database with:
    - Native metadata filtering (pre-retrieval)
    - Automatic scaling
    - No local persistence needed

    Requires:
    - PINECONE_API_KEY in environment
    - PINECONE_INDEX_NAME (default: deal-intelligence)
    """

    def __init__(self):
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not configured")

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.pc.Index(settings.pinecone_index_name)

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small",
        )

        # Local content cache (Pinecone doesn't store full text by default)
        self._content_cache: dict[str, str] = {}

        # Embedding dimension for zero-vector queries
        self.embedding_dim = 1536  # text-embedding-3-small dimension

    @property
    def count(self) -> int:
        """Number of vectors in the index."""
        try:
            stats = self.index.describe_index_stats()
            return stats.total_vector_count
        except Exception as e:
            logger.warning(f"Failed to get index stats: {e}")
            return 0

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add chunks to Pinecone.

        Args:
            chunks: List of chunks to add

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        # Prepare vectors for upsert
        vectors = []
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self.embeddings.embed_query(chunk.content)

            # Create unique ID
            vector_id = f"{chunk.metadata.doc_id}_{chunk.chunk_index}"

            # Store content in cache
            self._content_cache[vector_id] = chunk.content

            # Prepare metadata (Pinecone has limits on metadata size)
            raw_metadata = chunk.to_dict()
            # Filter out None values - Pinecone doesn't accept nulls
            metadata = {k: v for k, v in raw_metadata.items() if v is not None}
            # Truncate content for metadata (Pinecone limit ~40KB per vector)
            metadata["content_preview"] = chunk.content[:500]

            vectors.append(
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata,
                }
            )

        # Upsert in batches (Pinecone limit: 100 vectors per upsert)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self.index.upsert(vectors=batch)

        logger.info(f"Added {len(chunks)} chunks to Pinecone")
        return len(chunks)

    def search(self, query: SearchQuery) -> SearchResponse:
        """Search Pinecone with optional metadata filters.

        Args:
            query: Search query with optional filters

        Returns:
            Search results with scores and metadata
        """
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query.query)

        # Build filter if provided
        pinecone_filter = None
        if query.filters:
            pinecone_filter = self._build_pinecone_filter(query.filters)

        # Search
        response = self.index.query(
            vector=query_embedding,
            top_k=query.top_k,
            include_metadata=True,
            filter=pinecone_filter,
        )

        # Convert to SearchResults
        results = []
        for match in response.matches:
            metadata = match.metadata or {}

            # Get full content from cache or use preview
            content = self._content_cache.get(
                match.id, metadata.get("content_preview", "")
            )

            results.append(
                SearchResult(
                    content=content,
                    score=round(match.score, 4),
                    metadata=metadata,
                )
            )

        return SearchResponse(
            results=results,
            total_searched=self.count,
            query=query.query,
        )

    def _build_pinecone_filter(self, filters: dict[str, Any]) -> dict:
        """Convert our filter format to Pinecone filter format."""
        # Simple exact match filters
        pinecone_filter = {}
        for key, value in filters.items():
            pinecone_filter[key] = {"$eq": value}
        return pinecone_filter

    def clear(self) -> None:
        """Clear all vectors from the index."""
        try:
            self.index.delete(delete_all=True)
            self._content_cache.clear()
            logger.info("Cleared Pinecone index")
        except Exception as e:
            logger.error(f"Failed to clear Pinecone index: {e}")

    def save(self, path: Path) -> None:
        """No-op for Pinecone (managed service)."""
        logger.debug("Pinecone is a managed service - no local save needed")

    def load(self, path: Path) -> None:
        """No-op for Pinecone (managed service)."""
        logger.debug("Pinecone is a managed service - no local load needed")

    def get_all_metadata(self) -> list[dict]:
        """Get metadata for all stored chunks.

        Warning:
            NOT production-ready. This queries all vectors from Pinecone
            which is slow and expensive. For production, use a separate
            document registry (SQLite/Postgres) to track indexed documents.
        """
        if self.count == 0:
            return []

        # Use a zero vector to fetch all results (sorted by cosine similarity)
        # This is a workaround since Pinecone doesn't have a native list operation
        zero_vector = [0.0] * self.embedding_dim
        response = self.index.query(
            vector=zero_vector,
            top_k=min(10000, self.count),  # Pinecone limit
            include_metadata=True,
        )

        metadata_list = []
        for match in getattr(response, "matches", []):
            metadata = dict(getattr(match, "metadata", {}) or {})
            metadata.pop("content", None)  # Remove content from metadata
            metadata_list.append(metadata)

        return metadata_list
