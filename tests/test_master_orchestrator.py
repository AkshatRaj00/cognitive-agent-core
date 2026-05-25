"""Unit tests for master_orchestrator.MasterOrchestrator."""

import pytest
from master_orchestrator import MasterOrchestrator


def test_enqueue_and_run_next():
    orch = MasterOrchestrator()
    orch.enqueue("t1", lambda: "result1")
    result = orch.run_next()
    assert result == "result1"


def test_priority_ordering():
    orch = MasterOrchestrator()
    order = []
    orch.enqueue("low", lambda: order.append("low"), priority=10)
    orch.enqueue("high", lambda: order.append("high"), priority=1)
    orch.enqueue("mid", lambda: order.append("mid"), priority=5)
    orch.run_all()
    assert order == ["high", "mid", "low"]


def test_fifo_within_same_priority():
    orch = MasterOrchestrator()
    order = []
    orch.enqueue("first", lambda: order.append("first"), priority=5)
    orch.enqueue("second", lambda: order.append("second"), priority=5)
    orch.run_all()
    assert order == ["first", "second"]


def test_lifecycle_hooks():
    started, succeeded = [], []
    orch = MasterOrchestrator(
        on_task_start=lambda name: started.append(name),
        on_task_success=lambda name, result: succeeded.append(name),
    )
    orch.enqueue("job", lambda: "done")
    orch.run_next()
    assert "job" in started
    assert "job" in succeeded


def test_run_next_on_empty_queue():
    orch = MasterOrchestrator()
    assert orch.run_next() is None


def test_pending_count():
    orch = MasterOrchestrator()
    assert orch.pending_count == 0
    orch.enqueue("a", lambda: None)
    orch.enqueue("b", lambda: None)
    assert orch.pending_count == 2
    orch.run_next()
    assert orch.pending_count == 1
