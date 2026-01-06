"""Memory layer with vector store implementations.

This module provides:
- vector_store: Singleton vector store instance (configured via settings)
- VectorStoreRepository: Abstract interface for vector stores
- INDEX_PATH, KNOWLEDGE_BASE_PATH: Project paths (from app.constants)
"""

from app.constants import INDEX_PATH, KNOWLEDGE_BASE_PATH
from app.memory.base import VectorStoreRepository
from app.memory.factory import vector_store

__all__ = [
    "vector_store",
    "INDEX_PATH",
    "KNOWLEDGE_BASE_PATH",
    "VectorStoreRepository",
]
