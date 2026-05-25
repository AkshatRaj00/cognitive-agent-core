"""core_telemetry.py — Lightweight structured telemetry / event tracing."""

import time
import json
import threading
from dataclasses import dataclass, asdict, field
from typing import Any, Optional
from collections import deque


@dataclass
class TelemetryEvent:
    """A single structured telemetry event."""
    event_type: str
    timestamp: float = field(default_factory=time.time)
    duration_ms: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


class Telemetry:
    """Thread-safe telemetry sink with an in-memory ring buffer.

    Events are stored in a bounded deque (ring buffer) so memory usage
    is capped regardless of runtime duration.
    """

    def __init__(self, max_events: int = 500, enabled: bool = True):
        self._buffer: deque[TelemetryEvent] = deque(maxlen=max_events)
        self._lock = threading.Lock()
        self.enabled = enabled
        self._counters: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(self, event_type: str, *, duration_ms: Optional[float] = None,
               metadata: Optional[dict] = None, success: bool = True,
               error: Optional[str] = None) -> None:
        """Record a telemetry event."""
        if not self.enabled:
            return
        event = TelemetryEvent(
            event_type=event_type,
            duration_ms=duration_ms,
            metadata=metadata or {},
            success=success,
            error=error,
        )
        with self._lock:
            self._buffer.append(event)
            self._counters[event_type] = self._counters.get(event_type, 0) + 1

    def timed(self, event_type: str, metadata: Optional[dict] = None):
        """Context manager that records an event with automatic duration.

        Usage::

            with telemetry.timed("llm.call", metadata={"model": "gemini-pro"}):
                response = model.generate(prompt)
        """
        return _TimedEvent(self, event_type, metadata or {})

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def events(self, event_type: Optional[str] = None) -> list[TelemetryEvent]:
        """Return a snapshot of buffered events, optionally filtered by type."""
        with self._lock:
            if event_type is None:
                return list(self._buffer)
            return [e for e in self._buffer if e.event_type == event_type]

    def count(self, event_type: str) -> int:
        """Total number of times *event_type* has been recorded (lifetime)."""
        with self._lock:
            return self._counters.get(event_type, 0)

    def summary(self) -> dict[str, Any]:
        """Return a dict summarising event counts and average durations."""
        with self._lock:
            result: dict[str, Any] = {}
            for etype in set(e.event_type for e in self._buffer):
                evts = [e for e in self._buffer if e.event_type == etype]
                durations = [e.duration_ms for e in evts if e.duration_ms is not None]
                result[etype] = {
                    "count": self._counters.get(etype, 0),
                    "success_rate": sum(1 for e in evts if e.success) / len(evts),
                    "avg_duration_ms": (sum(durations) / len(durations)) if durations else None,
                }
            return result

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()


class _TimedEvent:
    """Internal context manager used by Telemetry.timed()."""

    def __init__(self, telemetry: Telemetry, event_type: str, metadata: dict):
        self._telemetry = telemetry
        self._event_type = event_type
        self._metadata = metadata
        self._start: float = 0.0
        self.error: Optional[str] = None

    def __enter__(self) -> "_TimedEvent":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        duration_ms = (time.perf_counter() - self._start) * 1000
        self._telemetry.record(
            self._event_type,
            duration_ms=duration_ms,
            metadata=self._metadata,
            success=exc_type is None,
            error=str(exc_val) if exc_val else None,
        )
        return False  # don't suppress exceptions
