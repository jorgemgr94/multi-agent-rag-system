"""Document ingestion pipeline.

This module provides:
- IngestionPipeline: End-to-end document loading and chunking
- DocumentLoader: Load documents from the knowledge base
- DocumentChunker: Chunk documents with type-specific strategies
"""

from app.ingestion.chunker import CHUNK_CONFIG, DEFAULT_CHUNK_CONFIG, DocumentChunker
from app.ingestion.loader import DocumentLoader
from app.ingestion.pipeline import IngestionPipeline

__all__ = [
    "IngestionPipeline",
    "DocumentLoader",
    "DocumentChunker",
    "CHUNK_CONFIG",
    "DEFAULT_CHUNK_CONFIG",
]
