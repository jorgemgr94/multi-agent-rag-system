"""Document chunking with type-specific strategies."""

import re

import tiktoken

from app.core import get_logger
from app.documents.schemas import Chunk, DocType, Document

logger = get_logger(__name__)


# Chunking configuration per document type
CHUNK_CONFIG = {
    DocType.DEAL: {"chunk_size": 1000, "overlap": 200},
    DocType.PROPOSAL: {"chunk_size": 500, "overlap": 100},
    DocType.COMPETITOR: {"chunk_size": 800, "overlap": 150},
    DocType.PRODUCT: {"chunk_size": 500, "overlap": 100},
    DocType.CASE_STUDY: {"chunk_size": 800, "overlap": 150},
    DocType.INDUSTRY: {"chunk_size": 600, "overlap": 120},
    DocType.RECORDING: {"chunk_size": 800, "overlap": 150},
}

DEFAULT_CHUNK_CONFIG = {"chunk_size": 500, "overlap": 100}


class DocumentChunker:
    """Chunks documents based on type-specific strategies."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize chunker with tokenizer.

        Args:
            model: Model name for tiktoken encoding
        """
        self.encoding = tiktoken.encoding_for_model(model)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def chunk_document(self, document: Document) -> list[Chunk]:
        """Split a document into chunks based on its type.

        Args:
            document: Document to chunk

        Returns:
            List of chunks with metadata
        """
        doc_type = document.metadata.doc_type
        config = CHUNK_CONFIG.get(doc_type, DEFAULT_CHUNK_CONFIG)

        chunk_size = config["chunk_size"]
        overlap = config["overlap"]

        # Split by paragraphs first
        paragraphs = self._split_paragraphs(document.content)

        # Merge paragraphs into chunks respecting token limits
        chunks = self._merge_into_chunks(paragraphs, chunk_size, overlap)

        # Create Chunk objects with metadata
        total_chunks = len(chunks)
        result = []
        for i, chunk_text in enumerate(chunks):
            result.append(
                Chunk(
                    content=chunk_text,
                    metadata=document.metadata,
                    chunk_index=i,
                    total_chunks=total_chunks,
                )
            )

        logger.debug(
            f"Chunked {document.metadata.doc_id}: {total_chunks} chunks "
            f"(config: {chunk_size}/{overlap})"
        )
        return result

    def _split_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        # Split on double newlines or markdown headers
        paragraphs = re.split(r"\n\n+|(?=^#{1,3}\s)", text, flags=re.MULTILINE)
        return [p.strip() for p in paragraphs if p.strip()]

    def _merge_into_chunks(
        self, paragraphs: list[str], chunk_size: int, overlap: int
    ) -> list[str]:
        """Merge paragraphs into chunks respecting token limits."""
        chunks = []
        current_chunk: list[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.count_tokens(para)

            # If single paragraph exceeds chunk size, split it
            if para_tokens > chunk_size:
                # Flush current chunk
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split large paragraph by sentences
                sentences = self._split_sentences(para)
                for sentence in sentences:
                    sent_tokens = self.count_tokens(sentence)
                    if current_tokens + sent_tokens > chunk_size and current_chunk:
                        chunks.append(" ".join(current_chunk))
                        # Keep overlap
                        overlap_text = " ".join(current_chunk)[-overlap:]
                        current_chunk = [overlap_text] if overlap_text else []
                        current_tokens = self.count_tokens(overlap_text)
                    current_chunk.append(sentence)
                    current_tokens += sent_tokens
                continue

            # Check if adding paragraph exceeds limit
            if current_tokens + para_tokens > chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # Keep some overlap from the end
                overlap_text = current_chunk[-1] if current_chunk else ""
                overlap_tokens = self.count_tokens(overlap_text)
                if overlap_tokens <= overlap:
                    current_chunk = [overlap_text]
                    current_tokens = overlap_tokens
                else:
                    current_chunk = []
                    current_tokens = 0

            current_chunk.append(para)
            current_tokens += para_tokens

        # Flush remaining
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]
