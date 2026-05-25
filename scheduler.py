"""scheduler.py — TaskScheduler with cron-style recurring jobs and priority queue."""

from __future__ import annotations

import heapq
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass(order=True)
class ScheduledTask:
    """A task queued for future execution."""
    run_at: float                              # epoch seconds (sort key)
    priority: int = field(default=50)          # lower = higher priority
    task_id: str = field(default_factory=lambda: str(uuid4()), compare=False)
    name: str = field(default="", compare=False)
    fn: Callable[..., Any] = field(default=lambda: None, compare=False)
    kwargs: dict[str, Any] = field(default_factory=dict, compare=False)
    interval: Optional[float] = field(default=None, compare=False)  # seconds, None = one-shot
    cancel_flag: threading.Event = field(default_factory=threading.Event, compare=False)

    @property
    def is_recurring(self) -> bool:
        return self.interval is not None

    def cancel(self) -> None:
        self.cancel_flag.set()

    @property
    def cancelled(self) -> bool:
        return self.cancel_flag.is_set()


class TaskScheduler:
    """A thread-safe task scheduler with one-shot and recurring job support.

    Jobs are stored in a min-heap ordered by (run_at, priority). A daemon
    worker thread wakes up, executes due jobs, and re-queues recurring ones.

    Example::

        scheduler = TaskScheduler()
        scheduler.start()

        # Run once in 5 seconds
        scheduler.schedule_once("cleanup", cleanup_fn, delay=5)

        # Run every 60 seconds
        scheduler.schedule_recurring("heartbeat", ping_fn, interval=60)

        scheduler.stop()
    """

    def __init__(self, poll_interval: float = 0.5) -> None:
        self._heap: list[ScheduledTask] = []
        self._heap_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._poll_interval = poll_interval
        self._worker: Optional[threading.Thread] = None
        self._completed: int = 0
        self._failed: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background worker thread."""
        if self._worker and self._worker.is_alive():
            return
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._run_loop, daemon=True, name="TaskScheduler")
        self._worker.start()
        logger.info("TaskScheduler started.")

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the worker to stop and wait for it."""
        self._stop_event.set()
        if self._worker:
            self._worker.join(timeout=timeout)
        logger.info("TaskScheduler stopped. completed=%d failed=%d", self._completed, self._failed)

    # ------------------------------------------------------------------
    # Scheduling API
    # ------------------------------------------------------------------

    def schedule_once(
        self,
        name: str,
        fn: Callable[..., Any],
        *,
        delay: float = 0.0,
        priority: int = 50,
        **kwargs: Any,
    ) -> ScheduledTask:
        """Schedule *fn* to run once after *delay* seconds."""
        task = ScheduledTask(
            run_at=time.time() + delay,
            priority=priority,
            name=name,
            fn=fn,
            kwargs=kwargs,
        )
        self._push(task)
        return task

    def schedule_recurring(
        self,
        name: str,
        fn: Callable[..., Any],
        *,
        interval: float,
        delay: float = 0.0,
        priority: int = 50,
        **kwargs: Any,
    ) -> ScheduledTask:
        """Schedule *fn* to run every *interval* seconds, starting after *delay*."""
        task = ScheduledTask(
            run_at=time.time() + delay,
            priority=priority,
            name=name,
            fn=fn,
            kwargs=kwargs,
            interval=interval,
        )
        self._push(task)
        return task

    def cancel_all(self, name: str) -> int:
        """Cancel all tasks matching *name*. Returns count cancelled."""
        count = 0
        with self._heap_lock:
            for task in self._heap:
                if task.name == name and not task.cancelled:
                    task.cancel()
                    count += 1
        return count

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _push(self, task: ScheduledTask) -> None:
        with self._heap_lock:
            heapq.heappush(self._heap, task)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            now = time.time()
            tasks_to_run: list[ScheduledTask] = []
            with self._heap_lock:
                while self._heap and self._heap[0].run_at <= now:
                    tasks_to_run.append(heapq.heappop(self._heap))
            for task in tasks_to_run:
                if task.cancelled:
                    continue
                try:
                    task.fn(**task.kwargs)
                    self._completed += 1
                    logger.debug("Task '%s' executed (id=%s)", task.name, task.task_id[:8])
                except Exception as exc:  # noqa: BLE001
                    self._failed += 1
                    logger.warning("Task '%s' raised: %s", task.name, exc)
                if task.is_recurring and not task.cancelled:
                    task.run_at = time.time() + task.interval  # type: ignore[operator]
                    self._push(task)
            time.sleep(self._poll_interval)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def queue_size(self) -> int:
        with self._heap_lock:
            return len(self._heap)

    def stats(self) -> dict[str, int]:
        return {"completed": self._completed, "failed": self._failed, "queued": self.queue_size}
