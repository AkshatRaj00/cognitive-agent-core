"""tracer.py — Lightweight OpenTelemetry-compatible span tracer for agent observability."""

from __future__ import annotations

import contextlib
import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Generator, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """A single trace span representing a unit of work."""
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "OK"          # OK | ERROR
    error_message: Optional[str] = None

    @property
    def duration_ms(self) -> float:
        """Wall-clock duration in milliseconds (0 if not ended)."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, **attrs: Any) -> None:
        self.events.append({"name": name, "timestamp": time.perf_counter(), **attrs})

    def record_exception(self, exc: Exception) -> None:
        self.status = "ERROR"
        self.error_message = str(exc)
        self.add_event("exception", type=type(exc).__name__, message=str(exc))

    def end(self) -> None:
        if self.end_time is None:
            self.end_time = time.perf_counter()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "duration_ms": round(self.duration_ms, 3),
            "status": self.status,
            "error": self.error_message,
            "attributes": self.attributes,
            "events": self.events,
        }


_local = threading.local()


class Tracer:
    """Context-manager-based span tracer.

    Spans are stored in-memory and can be exported via ``flush()``.
    Supports parent–child nesting using thread-local state.

    Example::

        tracer = Tracer(service_name="cognitive-agent-core")

        with tracer.span("handle_request") as span:
            span.set_attribute("user_id", "u123")
            with tracer.span("call_llm") as inner:
                inner.set_attribute("model", "gemini-1.5-pro")
    """

    def __init__(self, service_name: str = "agent", max_spans: int = 10_000) -> None:
        self.service_name = service_name
        self._spans: list[Span] = []
        self._max_spans = max_spans
        self._lock = threading.Lock()

    @contextlib.contextmanager
    def span(
        self,
        name: str,
        *,
        trace_id: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> Generator[Span, None, None]:
        """Context manager that creates, yields, and finalises a span."""
        parent_id: Optional[str] = getattr(_local, "current_span_id", None)
        tid = trace_id or getattr(_local, "current_trace_id", None) or uuid4().hex

        span = Span(
            name=name,
            trace_id=tid,
            parent_span_id=parent_id,
            attributes={"service": self.service_name, **(attributes or {})},
        )

        # Set thread-local context
        prev_span_id = getattr(_local, "current_span_id", None)
        prev_trace_id = getattr(_local, "current_trace_id", None)
        _local.current_span_id = span.span_id
        _local.current_trace_id = tid

        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            raise
        finally:
            span.end()
            _local.current_span_id = prev_span_id
            _local.current_trace_id = prev_trace_id
            self._record(span)
            logger.debug(
                "[trace] %s %s %.1fms %s",
                span.trace_id[:8], span.name, span.duration_ms, span.status,
            )

    def _record(self, span: Span) -> None:
        with self._lock:
            if len(self._spans) >= self._max_spans:
                self._spans = self._spans[-(self._max_spans // 2) :]   # drop oldest half
            self._spans.append(span)

    def flush(self) -> list[dict[str, Any]]:
        """Return all recorded spans as dicts and clear the buffer."""
        with self._lock:
            result = [s.to_dict() for s in self._spans]
            self._spans.clear()
        return result

    @property
    def span_count(self) -> int:
        with self._lock:
            return len(self._spans)
