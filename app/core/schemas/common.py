"""Core schemas for the multi-agent system."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Task Input Schema
# =============================================================================


class TaskInput(BaseModel):
    """Input schema for agent tasks."""

    task: str = Field(..., description="The task description to process")
    context: dict[str, Any] | None = Field(
        default=None, description="Optional context or metadata"
    )


# =============================================================================
# Agent Decision Schema
# =============================================================================


class DecisionType(str, Enum):
    """Types of decisions an agent can make."""

    USE_TOOL = "use_tool"
    RESPOND = "respond"
    CLARIFY = "clarify"
    ESCALATE = "escalate"
    DELEGATE = "delegate"
    RETRIEVE = "retrieve"


class ToolCall(BaseModel):
    """Schema for a tool invocation."""

    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments to pass to the tool"
    )


class AgentDecision(BaseModel):
    """Structured decision output from an agent."""

    decision_type: DecisionType = Field(..., description="The type of decision made")
    reasoning: str = Field(..., description="Internal reasoning")
    tool_call: ToolCall | None = Field(default=None)
    message: str | None = Field(default=None)
    delegate_to: str | None = Field(
        default=None, description="Target agent for delegation"
    )


# =============================================================================
# Observation Schema
# =============================================================================


class Observation(BaseModel):
    """Observation from a tool or retrieval execution."""

    source: str = Field(..., description="Tool name or 'retrieval'")
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None


# =============================================================================
# Agent Response Schema
# =============================================================================


class ResponseStatus(str, Enum):
    """Status of the final response."""

    SUCCESS = "success"
    FAILED = "failed"
    NEEDS_INPUT = "needs_input"
    ESCALATED = "escalated"


class AgentResponse(BaseModel):
    """Final structured response."""

    status: ResponseStatus
    message: str
    data: dict[str, Any] | None = None


# =============================================================================
# API Models
# =============================================================================


class TaskRequest(BaseModel):
    """API request model."""

    task: str = Field(..., description="The task to process")
    context: dict[str, Any] | None = Field(default=None)

    def to_task_input(self) -> TaskInput:
        return TaskInput(task=self.task, context=self.context)


class TaskResponse(BaseModel):
    """API response model."""

    status: ResponseStatus
    message: str
    data: dict[str, Any] | None = None

    @classmethod
    def from_agent_response(cls, response: AgentResponse) -> "TaskResponse":
        return cls(
            status=response.status,
            message=response.message,
            data=response.data,
        )
