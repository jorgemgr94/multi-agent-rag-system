"""Schema validation tests."""

import pytest
from pydantic import ValidationError

from app.core.schemas import DecisionType, TaskInput


def test_task_input_valid():
    task = TaskInput(task="Do something")
    assert task.task == "Do something"


def test_task_input_missing_task():
    with pytest.raises(ValidationError):
        TaskInput()  # type: ignore


def test_decision_type_includes_p2_types():
    assert DecisionType.DELEGATE.value == "delegate"
    assert DecisionType.RETRIEVE.value == "retrieve"
