"""tool_registry.py — Dynamic ToolRegistry for cognitive agent tool management."""

import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Metadata descriptor for a registered tool."""
    name: str
    description: str
    fn: Callable[..., Any]
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    call_count: int = field(default=0, init=False)

    def invoke(self, **kwargs: Any) -> Any:
        """Call the underlying function, incrementing the counter."""
        if not self.enabled:
            raise RuntimeError(f"Tool '{self.name}' is disabled.")
        self.call_count += 1
        logger.debug("Invoking tool '%s' (call #%d)", self.name, self.call_count)
        return self.fn(**kwargs)

    @property
    def signature(self) -> str:
        """Human-readable signature string for introspection."""
        sig = inspect.signature(self.fn)
        return f"{self.name}{sig}"


class ToolRegistry:
    """Central registry for agent tools.

    Tools can be registered via:
    - ``register(name, fn, ...)``  — explicit registration
    - ``@registry.tool(...)``       — decorator style

    Example::

        registry = ToolRegistry()

        @registry.tool(description="Search the web", tags=["web"])
        def web_search(query: str) -> str:
            ...

        result = registry.invoke("web_search", query="Python asyncio")
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        fn: Callable[..., Any],
        *,
        description: str = "",
        tags: Optional[list[str]] = None,
        enabled: bool = True,
    ) -> ToolDefinition:
        """Register *fn* under *name*, replacing any existing tool with the same name."""
        if not callable(fn):
            raise TypeError(f"fn must be callable, got {type(fn).__name__}")
        definition = ToolDefinition(
            name=name,
            description=description,
            fn=fn,
            tags=tags or [],
            enabled=enabled,
        )
        self._tools[name] = definition
        logger.info("Registered tool '%s' (tags=%s)", name, definition.tags)
        return definition

    def tool(
        self,
        *,
        description: str = "",
        tags: Optional[list[str]] = None,
        enabled: bool = True,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator factory that registers the decorated function."""

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.register(
                fn.__name__,
                fn,
                description=description or (fn.__doc__ or "").strip().split("\n")[0],
                tags=tags,
                enabled=enabled,
            )
            return fn

        return decorator

    # ------------------------------------------------------------------
    # Invocation
    # ------------------------------------------------------------------

    def invoke(self, name: str, **kwargs: Any) -> Any:
        """Invoke a registered tool by name."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool '{name}'. Available: {self.list_names()}")
        return self._tools[name].invoke(**kwargs)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Return the ToolDefinition for *name*, or None."""
        return self._tools.get(name)

    def list_names(self) -> list[str]:
        """Return sorted list of all registered tool names."""
        return sorted(self._tools.keys())

    def list_by_tag(self, tag: str) -> list[ToolDefinition]:
        """Return all tools whose tags include *tag*."""
        return [t for t in self._tools.values() if tag in t.tags]

    def enable(self, name: str) -> None:
        """Enable a previously disabled tool."""
        self._get_or_raise(name).enabled = True

    def disable(self, name: str) -> None:
        """Disable a tool without removing it."""
        self._get_or_raise(name).enabled = False

    def summary(self) -> list[dict[str, Any]]:
        """Return a list of dicts suitable for JSON serialisation."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "tags": t.tags,
                "enabled": t.enabled,
                "call_count": t.call_count,
                "signature": t.signature,
            }
            for t in self._tools.values()
        ]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def _get_or_raise(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found.")
        return self._tools[name]
