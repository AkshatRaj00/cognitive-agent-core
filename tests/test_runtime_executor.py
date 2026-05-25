"""Unit tests for runtime_executor.RuntimeExecutor."""

import pytest
from runtime_executor import RuntimeExecutor, ExecutionError


def test_successful_execution():
    executor = RuntimeExecutor(max_retries=0)
    result = executor.execute(lambda: 42)
    assert result == 42


def test_retries_on_failure():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("not yet")
        return "ok"

    executor = RuntimeExecutor(max_retries=3, backoff_base=0.01)
    result = executor.execute(flaky)
    assert result == "ok"
    assert len(calls) == 3


def test_raises_after_exhausting_retries():
    executor = RuntimeExecutor(max_retries=2, backoff_base=0.01)
    with pytest.raises(ExecutionError) as exc_info:
        executor.execute(lambda: (_ for _ in ()).throw(ValueError("boom")), task_name="bad_task")
    assert exc_info.value.attempts == 3


def test_execute_with_fallback():
    executor = RuntimeExecutor(max_retries=0, backoff_base=0.01)
    result = executor.execute_with_fallback(
        lambda: (_ for _ in ()).throw(RuntimeError("fail")),
        fallback="default",
    )
    assert result == "default"


def test_invalid_max_retries():
    with pytest.raises(ValueError):
        RuntimeExecutor(max_retries=-1)
