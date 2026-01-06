"""Pinecone vector store implementation."""

from pathlib import Path
from typing import Any

from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

from app.config import settings
from app.logging_config import get_logger
from app.memory.base import VectorStoreRepository
from app.schemas.document import Chunk, SearchQuery, SearchResponse, SearchResult

logger = get_logger(__name__)


class PineconeVectorStore(VectorStoreRepository):
    """Pinecone-based vector store implementation.

    Supports:
    - Semantic search via embeddings
    - Native metadata filtering (pre-retrieval, more efficient than FAISS)
    - Cloud-managed persistence

    Requires:
    - PINECONE_API_KEY in environment
    - PINECONE_INDEX_NAME in environment
    """

    def __init__(
        self,
        api_key: str | None = None,
        index_name: str | None = None,
        environment: str | None = None,
        embedding_dim: int = 1536,
        create_if_missing: bool = True,
    ):
        self.api_key = api_key or settings.pinecone_api_key
        self.index_name = index_name or settings.pinecone_index_name
        self.environment = environment or settings.pinecone_environment
        self.embedding_dim = embedding_dim

        if not self.api_key:
            raise ValueError("PINECONE_API_KEY is required")
        if not self.index_name:
            raise ValueError("PINECONE_INDEX_NAME is required")

        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)

        # Create index if it doesn't exist
        if create_if_missing:
            self._ensure_index_exists()

        # Connect to index
        self.index = self.pc.Index(self.index_name)

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small",
        )

        logger.info(f"Connected to Pinecone index: {self.index_name}")

    def _ensure_index_exists(self) -> None:
        """Create the index if it doesn't exist."""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dim,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.environment or "us-east-1",
                ),
            )
            logger.info(f"Created index: {self.index_name}")

    @property
    def count(self) -> int:
        """Number of vectors in the index."""
        stats = self.index.describe_index_stats()
        return stats.total_vector_count

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add chunks to the vector store.

        Args:
            chunks: List of chunks to add

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        # Extract content for embedding
        texts = [chunk.content for chunk in chunks]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embeddings.embed_documents(texts)

        # Prepare vectors for upsert
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            metadata = chunk.to_dict()
            # Store content in metadata for retrieval
            metadata["content"] = chunk.content

            # Pinecone doesn't accept null values - filter them out
            clean_metadata = {k: v for k, v in metadata.items() if v is not None}

            vectors.append(
                {
                    "id": f"{chunk.metadata.doc_id}_{chunk.chunk_index}",
                    "values": embedding,
                    "metadata": clean_metadata,
                }
            )

        # Upsert in batches (Pinecone limit is 100 per request)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            self.index.upsert(vectors=batch)

        logger.info(f"Added {len(chunks)} chunks to Pinecone. Total: {self.count}")
        return len(chunks)

    def search(self, query: SearchQuery) -> SearchResponse:
        """Search the vector store.

        Args:
            query: Search query with optional filters

        Returns:
            Search results with scores and metadata
        """
        if self.count == 0:
            return SearchResponse(
                results=[],
                total_searched=0,
                query=query.query,
            )

        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query.query)

        # Build Pinecone filter from our filters
        pinecone_filter = None
        if query.filters:
            pinecone_filter = self._build_pinecone_filter(query.filters)

        # Query Pinecone
        response = self.index.query(
            vector=query_embedding,
            top_k=query.top_k,
            filter=pinecone_filter,
            include_metadata=True,
        )

        # Convert to our response format
        results = []
        # Handle both dict and object response types from Pinecone SDK
        matches = getattr(response, "matches", [])
        for match in matches:
            metadata = dict(getattr(match, "metadata", {}) or {})
            score = getattr(match, "score", 0.0)
            content = metadata.pop("content", "")

            results.append(
                SearchResult(
                    content=content,
                    score=round(score, 4),
                    metadata=metadata,
                )
            )

        return SearchResponse(
            results=results,
            total_searched=self.count,
            query=query.query,
        )

    def _build_pinecone_filter(self, filters: dict[str, Any]) -> dict:
        """Convert our filter format to Pinecone filter format.

        Our format: {"doc_type": "deal", "industry": "healthcare"}
        Pinecone: {"doc_type": {"$eq": "deal"}, "industry": {"$eq": "healthcare"}}
        """
        pinecone_filter = {}
        for key, value in filters.items():
            if isinstance(value, list):
                # For list values, use $in operator
                pinecone_filter[key] = {"$in": value}
            else:
                # For scalar values, use $eq operator
                pinecone_filter[key] = {"$eq": value}
        return pinecone_filter

    def save(self, path: Path) -> None:
        """No-op for Pinecone (cloud-managed persistence)."""
        logger.info("Pinecone is cloud-managed, no local save needed")

    def load(self, path: Path) -> None:
        """No-op for Pinecone (cloud-managed persistence)."""
        logger.info("Pinecone is cloud-managed, no local load needed")

    def clear(self) -> None:
        """Clear all data from the index."""
        try:
            # Check if there's anything to delete first
            if self.count == 0:
                logger.info("Index is already empty, nothing to clear")
                return

            self.index.delete(delete_all=True)
            logger.info(f"Cleared all vectors from Pinecone index: {self.index_name}")
        except Exception as e:
            error_str = str(e).lower()
            # Pinecone returns 404 if namespace/index is empty - that's fine
            if "404" in error_str or "not found" in error_str:
                logger.info("Index appears empty, nothing to clear")
            else:
                logger.warning(f"Could not clear index: {e}")

    def delete_index(self) -> None:
        """Delete the entire index (use with caution!)."""
        self.pc.delete_index(self.index_name)
        logger.info(f"Deleted Pinecone index: {self.index_name}")

    def get_all_metadata(self) -> list[dict]:
        """Get metadata for all stored chunks.

        Warning:
            NOT production-ready. This queries all vectors from Pinecone
            which is slow and expensive. For production, use a separate
            document registry (SQLite/Postgres) to track indexed documents.
            See VectorStoreRepository.get_all_metadata for details.
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
