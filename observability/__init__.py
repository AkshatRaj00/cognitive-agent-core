"""observability package — distributed tracing and metrics for cognitive-agent-core."""

from .tracer import Span, Tracer

__all__ = ["Tracer", "Span"]
