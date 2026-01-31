"""Document agents module.

Contains agents for document retrieval and processing.
"""

from app.documents.agents.retriever import (
    DEFAULT_TOP_K,
    MAX_CONTEXT_TOKENS,
    MAX_TOP_K,
    MIN_RELEVANCE_SCORE,
    MIN_TOP_K,
    RetrieverAgent,
)

__all__ = [
    "RetrieverAgent",
    # Constants (exported for testing)
    "DEFAULT_TOP_K",
    "MAX_CONTEXT_TOKENS",
    "MAX_TOP_K",
    "MIN_RELEVANCE_SCORE",
    "MIN_TOP_K",
]
