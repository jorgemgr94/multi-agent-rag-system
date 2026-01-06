"""End-to-end document ingestion pipeline."""

from pathlib import Path

from app.ingestion.chunker import DocumentChunker
from app.ingestion.loader import DocumentLoader
from app.logging_config import get_logger
from app.schemas.document import Chunk

logger = get_logger(__name__)


class IngestionPipeline:
    """End-to-end document ingestion pipeline."""

    def __init__(self, knowledge_base_path: Path):
        self.loader = DocumentLoader(knowledge_base_path)
        self.chunker = DocumentChunker()

    def run(self) -> list[Chunk]:
        """Run full ingestion pipeline.

        Returns:
            List of chunks ready for vector store
        """
        # Load documents
        documents = self.loader.load_all()

        # Chunk all documents
        all_chunks: list[Chunk] = []
        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(
            f"Ingestion complete: {len(documents)} documents -> {len(all_chunks)} chunks"
        )
        return all_chunks
