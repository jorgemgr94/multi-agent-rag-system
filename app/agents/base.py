"""Base agent interface for multi-agent system."""

from abc import ABC, abstractmethod

from app.schemas.task import AgentDecision, Observation, TaskInput


class BaseAgent(ABC):
    """Abstract base class for all agents.

    Each agent has a specific responsibility:
    - PlannerAgent: Decomposes tasks, defines strategy
    - RetrieverAgent: Fetches relevant knowledge
    - ExecutorAgent: Executes automation actions
    - ValidatorAgent: Validates outputs
    """

    name: str
    description: str

    @abstractmethod
    def reason(
        self,
        task_input: TaskInput,
        observations: list[Observation] | None = None,
    ) -> AgentDecision:
        """Process a task and return a decision.

        Args:
            task_input: The task to process
            observations: Previous observations (tool results, retrievals)

        Returns:
            Structured decision
        """
        pass

    def get_schema(self) -> dict:
        """Return agent metadata for orchestration."""
        return {
            "name": self.name,
            "description": self.description,
        }
