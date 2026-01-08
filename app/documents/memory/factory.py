"""Vector store singleton."""

from app.core import settings
from app.core.constants import INDEX_PATH
from app.documents.memory.base import VectorStoreRepository


def _create_store() -> VectorStoreRepository:
    """Create the vector store based on config."""
    store_type = settings.vector_store_type.lower()

    if store_type == "faiss":
        from app.documents.memory.faiss_store import FAISSVectorStore

        return FAISSVectorStore(index_path=INDEX_PATH)

    if store_type == "pinecone":
        from app.documents.memory.pinecone_store import PineconeVectorStore

        return PineconeVectorStore()

    raise ValueError(f"Unsupported vector store type: {store_type}")


vector_store = _create_store()
