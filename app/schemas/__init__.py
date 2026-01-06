"""Schema definitions for the multi-agent system."""

from app.schemas.document import (
    Chunk,
    CompanySize,
    DealOutcome,
    DocType,
    Document,
    DocumentMetadata,
    SearchQuery,
    SearchResponse,
    SearchResult,
)
from app.schemas.task import (
    AgentDecision,
    AgentResponse,
    DecisionType,
    Observation,
    ResponseStatus,
    TaskInput,
    TaskRequest,
    TaskResponse,
    ToolCall,
)

__all__ = [
    # Document schemas
    "Chunk",
    "CompanySize",
    "DealOutcome",
    "DocType",
    "Document",
    "DocumentMetadata",
    "SearchQuery",
    "SearchResponse",
    "SearchResult",
    # Task schemas
    "AgentDecision",
    "AgentResponse",
    "DecisionType",
    "Observation",
    "ResponseStatus",
    "TaskInput",
    "TaskRequest",
    "TaskResponse",
    "ToolCall",
]
