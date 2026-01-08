"""FAISS vector store implementation."""

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.core import get_logger, settings
from app.documents.memory.base import VectorStoreRepository
from app.documents.schemas import Chunk, SearchQuery, SearchResponse, SearchResult

logger = get_logger(__name__)


class FAISSVectorStore(VectorStoreRepository):
    """FAISS-based vector store implementation.

    Uses inner product (cosine similarity) for scoring since OpenAI
    embeddings are normalized. Higher score = more similar.

    Supports:
    - Semantic search via embeddings
    - Metadata filtering (post-retrieval)
    - Persistence to disk

    Note: FAISS doesn't support native metadata filtering,
    so we filter post-retrieval. For production with large datasets,
    consider Pinecone which filters pre-retrieval.
    """

    def __init__(
        self,
        embedding_dim: int = 1536,  # OpenAI text-embedding-3-small
        index_path: Path | None = None,
    ):
        self.embedding_dim = embedding_dim
        self.index_path = index_path

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small",
        )

        # Inner product index (= cosine similarity for normalized vectors)
        self.index = faiss.IndexFlatIP(embedding_dim)

        # Metadata storage (FAISS doesn't store metadata natively)
        self.metadata_store: list[dict[str, Any]] = []
        self.content_store: list[str] = []

        # Load existing index if path provided
        if index_path and index_path.exists():
            self.load(index_path)

    @property
    def count(self) -> int:
        """Number of vectors in the index."""
        return self.index.ntotal

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
        embeddings_np = np.array(embeddings, dtype=np.float32)

        # Add to FAISS index
        self.index.add(embeddings_np)  # type: ignore[call-arg]

        # Store metadata and content
        for chunk in chunks:
            self.metadata_store.append(chunk.to_dict())
            self.content_store.append(chunk.content)

        logger.info(f"Added {len(chunks)} chunks. Total: {self.count}")
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
        query_np = np.array([query_embedding], dtype=np.float32)

        # Search with extra results for filtering
        # Fetch more than top_k to account for filtered results
        fetch_k = min(query.top_k * 3, self.count)
        scores, indices = self.index.search(query_np, fetch_k)  # type: ignore[call-arg]

        # Process results
        results: list[SearchResult] = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            metadata = self.metadata_store[idx]
            content = self.content_store[idx]

            # Apply metadata filters if provided
            if query.filters and not self._matches_filters(metadata, query.filters):
                continue

            # Inner product with normalized vectors = cosine similarity (0-1)
            score = float(scores[0][i])

            results.append(
                SearchResult(
                    content=content,
                    score=round(score, 4),
                    metadata=metadata,
                )
            )

            if len(results) >= query.top_k:
                break

        return SearchResponse(
            results=results,
            total_searched=self.count,
            query=query.query,
        )

    def _matches_filters(
        self, metadata: dict[str, Any], filters: dict[str, Any]
    ) -> bool:
        """Check if metadata matches all filters.

        Supports:
        - Exact match for strings/numbers
        - List membership for tags
        """
        for key, value in filters.items():
            if key not in metadata:
                return False

            meta_value = metadata[key]

            # Handle list membership (e.g., tags)
            if isinstance(meta_value, list):
                if value not in meta_value:
                    return False
            # Handle exact match
            elif meta_value != value:
                return False

        return True

    def save(self, path: Path) -> None:
        """Save index and metadata to disk."""
        path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))

        # Save metadata and content
        with open(path / "metadata.json", "w") as f:
            json.dump(
                {
                    "metadata": self.metadata_store,
                    "content": self.content_store,
                },
                f,
            )

        logger.info(f"Saved vector store to {path} ({self.count} vectors)")

    def load(self, path: Path) -> None:
        """Load index and metadata from disk."""
        index_file = path / "index.faiss"
        metadata_file = path / "metadata.json"

        if not index_file.exists() or not metadata_file.exists():
            logger.warning(f"No existing index found at {path}")
            return

        # Load FAISS index
        self.index = faiss.read_index(str(index_file))

        # Load metadata and content
        with open(metadata_file) as f:
            data = json.load(f)
            self.metadata_store = data["metadata"]
            self.content_store = data["content"]

        logger.info(f"Loaded vector store from {path} ({self.count} vectors)")

    def clear(self) -> None:
        """Clear all data from the store."""
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.metadata_store = []
        self.content_store = []
        logger.info("Cleared vector store")

    def get_all_metadata(self) -> list[dict]:
        """Get metadata for all stored chunks.

        Warning:
            O(n) operation. For production, use a document registry instead.
            See VectorStoreRepository.get_all_metadata for details.
        """
        return self.metadata_store
