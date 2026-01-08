"""Structured logging configuration for the multi-agent system."""

import logging
import sys
from typing import Any

# JSON-like structured log format for production
STRUCTURED_FORMAT = (
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
    '"module": "%(name)s", "message": "%(message)s"}'
)

# Human-readable format for development
DEV_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(
    level: str | int = "INFO",
    structured: bool = False,
) -> None:
    """Configure application logging.

    Args:
        level: Logging level as string or int (default: INFO)
        structured: Use JSON-structured format (default: False for dev)
    """
    log_format = STRUCTURED_FORMAT if structured else DEV_FORMAT

    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class AgentLogger:
    """Specialized logger for agent operations.

    Provides structured logging for agent decisions, tool calls,
    and observations with consistent formatting.
    """

    def __init__(self, agent_name: str):
        self.logger = get_logger(f"agent.{agent_name}")
        self.agent_name = agent_name

    def decision(self, decision_type: str, reasoning: str) -> None:
        """Log an agent decision."""
        self.logger.info(
            f"[DECISION] type={decision_type} reasoning={reasoning[:100]}..."
            if len(reasoning) > 100
            else f"[DECISION] type={decision_type} reasoning={reasoning}"
        )

    def tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Log a tool invocation."""
        self.logger.info(f"[TOOL_CALL] tool={tool_name} args={arguments}")

    def observation(self, source: str, success: bool, result: Any = None) -> None:
        """Log an observation from tool or retrieval."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"[OBSERVATION] source={source} status={status}")
        if result and not success:
            self.logger.debug(f"[OBSERVATION] result={result}")

    def error(self, message: str, exc: Exception | None = None) -> None:
        """Log an error."""
        self.logger.error(f"[ERROR] {message}", exc_info=exc)

    def info(self, message: str) -> None:
        """Log general info."""
        self.logger.info(message)
