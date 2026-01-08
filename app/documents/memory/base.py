"""Abstract base class for vector store implementations."""

from abc import ABC, abstractmethod
from pathlib import Path

from app.documents.schemas import Chunk, SearchQuery, SearchResponse


class VectorStoreRepository(ABC):
    """Abstract interface for vector stores.

    Implement this interface to create new vector store backends
    (e.g., FAISS, Pinecone, Weaviate, Qdrant, etc.)

    Example:
        class PineconeVectorStore(VectorStoreRepository):
            def add_chunks(self, chunks): ...
            def search(self, query): ...
    """

    @property
    @abstractmethod
    def count(self) -> int:
        """Number of vectors in the store."""
        pass

    @abstractmethod
    def add_chunks(self, chunks: list[Chunk]) -> int:
        """Add chunks to the vector store.

        Args:
            chunks: List of chunks to add

        Returns:
            Number of chunks added
        """
        pass

    @abstractmethod
    def search(self, query: SearchQuery) -> SearchResponse:
        """Search the vector store.

        Args:
            query: Search query with optional filters

        Returns:
            Search results with scores and metadata
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all data from the store."""
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """Persist the store to disk.

        Args:
            path: Directory to save to
        """
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        """Load the store from disk.

        Args:
            path: Directory to load from
        """
        pass

    @abstractmethod
    def get_all_metadata(self) -> list[dict]:
        """Get metadata for all stored chunks.

        Returns:
            List of metadata dictionaries

        Note:
            This is not production-ready. For production, use a separate
            document registry (SQLite/Postgres) instead of querying all
            vectors. Vector stores should only be used for semantic search,
            not inventory queries.
        """
        pass
