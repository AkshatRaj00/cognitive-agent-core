"""master_orchestrator.py — Priority task queue with agent lifecycle hooks."""

import heapq
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass(order=True)
class _PrioritizedTask:
    """Wrapper that makes tasks orderable by priority for heapq."""
    priority: int
    sequence: int           # tie-breaker: FIFO within same priority
    name: str = field(compare=False)
    task: Callable[[], Any] = field(compare=False)


class MasterOrchestrator:
    """Schedules and dispatches agent tasks via a thread-safe priority queue.

    Lower *priority* values run first (0 = highest priority).

    Lifecycle hooks:
        on_task_start(name)   — called just before a task executes
        on_task_success(name, result) — called on successful completion
        on_task_error(name, exc)      — called when a task raises
    """

    def __init__(
        self,
        on_task_start: Optional[Callable[[str], None]] = None,
        on_task_success: Optional[Callable[[str, Any], None]] = None,
        on_task_error: Optional[Callable[[str, Exception], None]] = None,
    ) -> None:
        self._heap: list[_PrioritizedTask] = []
        self._lock = threading.Lock()
        self._sequence = 0
        self.on_task_start = on_task_start or (lambda name: None)
        self.on_task_success = on_task_success or (lambda name, result: None)
        self.on_task_error = on_task_error or (lambda name, exc: None)
        self._results: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------

    def enqueue(self, name: str, task: Callable[[], Any], priority: int = 5) -> None:
        """Add a task to the queue.

        Args:
            name:     Unique identifier for the task (used in logs/hooks).
            task:     Zero-argument callable.
            priority: Integer priority; lower value = higher urgency.
        """
        with self._lock:
            seq = self._sequence
            self._sequence += 1
            heapq.heappush(self._heap, _PrioritizedTask(priority=priority, sequence=seq, name=name, task=task))
        logger.debug("Enqueued task '%s' with priority %d", name, priority)

    def run_next(self) -> Optional[Any]:
        """Pop and execute the highest-priority pending task.

        Returns the task's return value, or None if the queue was empty.
        """
        with self._lock:
            if not self._heap:
                return None
            item = heapq.heappop(self._heap)

        self.on_task_start(item.name)
        try:
            result = item.task()
            self._results[item.name] = result
            self.on_task_success(item.name, result)
            logger.info("Task '%s' completed successfully", item.name)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.error("Task '%s' raised: %s", item.name, exc)
            self.on_task_error(item.name, exc)
            raise

    def run_all(self) -> list[Any]:
        """Execute all queued tasks in priority order and return results."""
        results = []
        while self.pending_count > 0:
            results.append(self.run_next())
        return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._heap)

    def get_result(self, name: str) -> Any:
        """Return the stored result for a previously run task."""
        return self._results.get(name)

    def clear(self) -> None:
        with self._lock:
            self._heap.clear()
