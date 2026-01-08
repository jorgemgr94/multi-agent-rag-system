"""Vector store and ingestion tests."""

from pathlib import Path

import pytest

from app.documents.ingestion import DocumentChunker, DocumentLoader, IngestionPipeline
from app.documents.schemas import (
    Chunk,
    DocType,
    Document,
    DocumentMetadata,
    SearchQuery,
)

# Path to test knowledge base
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge_base"


class TestDocumentChunker:
    """Tests for document chunking."""

    def test_chunker_initializes(self):
        chunker = DocumentChunker()
        assert chunker is not None

    def test_count_tokens(self):
        chunker = DocumentChunker()
        tokens = chunker.count_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 10  # Simple phrase should be few tokens

    def test_chunk_document(self):
        chunker = DocumentChunker()

        metadata = DocumentMetadata(
            doc_id="test_doc",
            doc_type=DocType.DEAL,
            source_file="test.md",
        )
        doc = Document(
            content="This is a test document.\n\nIt has multiple paragraphs.\n\nAnd some content.",
            metadata=metadata,
        )

        chunks = chunker.chunk_document(doc)
        assert len(chunks) >= 1
        assert all(isinstance(c, Chunk) for c in chunks)
        assert chunks[0].metadata.doc_id == "test_doc"


class TestDocumentLoader:
    """Tests for document loading."""

    def test_loader_finds_documents(self):
        if not KNOWLEDGE_BASE_PATH.exists():
            pytest.skip("Knowledge base not found")

        loader = DocumentLoader(KNOWLEDGE_BASE_PATH)
        documents = loader.load_all()

        assert len(documents) > 0
        assert all(isinstance(d, Document) for d in documents)

    def test_loader_extracts_metadata(self):
        if not KNOWLEDGE_BASE_PATH.exists():
            pytest.skip("Knowledge base not found")

        loader = DocumentLoader(KNOWLEDGE_BASE_PATH)
        documents = loader.load_all()

        # Find a deal document
        deal_docs = [d for d in documents if d.metadata.doc_type == DocType.DEAL]
        assert len(deal_docs) > 0

        deal = deal_docs[0]
        assert deal.metadata.doc_id is not None
        assert deal.metadata.source_file is not None


class TestIngestionPipeline:
    """Tests for the full ingestion pipeline."""

    def test_pipeline_runs(self):
        if not KNOWLEDGE_BASE_PATH.exists():
            pytest.skip("Knowledge base not found")

        pipeline = IngestionPipeline(KNOWLEDGE_BASE_PATH)
        chunks = pipeline.run()

        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)


class TestSearchQuery:
    """Tests for search query schema."""

    def test_search_query_valid(self):
        query = SearchQuery(query="healthcare deals")
        assert query.query == "healthcare deals"
        assert query.top_k == 5  # default

    def test_search_query_with_filters(self):
        query = SearchQuery(
            query="similar deals",
            top_k=3,
            filters={"doc_type": "deal", "industry": "healthcare"},
        )
        assert query.filters is not None
        assert query.filters["doc_type"] == "deal"
