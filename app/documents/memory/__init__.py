"""Memory layer with vector store implementations."""

from app.documents.memory.base import VectorStoreRepository
from app.documents.memory.factory import vector_store


def get_vector_store() -> VectorStoreRepository:
    """Get the vector store singleton.

    Provides a clean interface for dependency injection.
    """
    return vector_store


__all__ = [
    "vector_store",
    "get_vector_store",
    "VectorStoreRepository",
]
