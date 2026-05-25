"""event_bus.py — Lightweight async EventBus for inter-component messaging."""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Immutable event envelope."""
    topic: str
    payload: Any
    event_id: str = field(default_factory=lambda: str(uuid4()))
    source: Optional[str] = None

    def __repr__(self) -> str:
        return f"Event(topic={self.topic!r}, id={self.event_id[:8]})"


Subscriber = Callable[[Event], Any]


class EventBus:
    """Publish-subscribe bus that supports synchronous and async subscribers.

    Features:
    - Topic-based routing (exact or wildcard ``'*'``)
    - Async subscriber support (coroutines are scheduled on the running loop)
    - Replay buffer: new subscribers can receive the last *N* events per topic

    Example::

        bus = EventBus(replay_size=10)

        @bus.subscribe("agent.response")
        def on_response(event: Event) -> None:
            print(event.payload)

        bus.publish("agent.response", payload={"text": "Hello!"})
    """

    def __init__(self, replay_size: int = 0) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}
        self._replay_size = replay_size
        self._replay_buffer: dict[str, deque[Event]] = {}

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(
        self,
        topic: str,
        *,
        replay: bool = False,
    ) -> Callable[[Subscriber], Subscriber]:
        """Decorator that registers a subscriber for *topic*.

        Args:
            topic:  Topic name, or ``'*'`` for all events.
            replay: If True, immediately deliver buffered events to the new subscriber.
        """

        def decorator(fn: Subscriber) -> Subscriber:
            self._subscribers.setdefault(topic, []).append(fn)
            logger.debug("Subscribed %s to topic '%s'", fn.__name__, topic)
            if replay and self._replay_size:
                for event in list(self._replay_buffer.get(topic, [])):
                    self._dispatch_one(fn, event)
            return fn

        return decorator

    def unsubscribe(self, topic: str, fn: Subscriber) -> bool:
        """Remove *fn* from *topic*. Returns True if it was present."""
        subs = self._subscribers.get(topic, [])
        try:
            subs.remove(fn)
            return True
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def publish(self, topic: str, payload: Any = None, *, source: Optional[str] = None) -> Event:
        """Create and dispatch an event to all matching subscribers."""
        event = Event(topic=topic, payload=payload, source=source)
        self._buffer(event)
        delivered = 0
        for sub in [*self._subscribers.get(topic, []), *self._subscribers.get("*", [])]:
            self._dispatch_one(sub, event)
            delivered += 1
        logger.debug("%r dispatched to %d subscriber(s)", event, delivered)
        return event

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _buffer(self, event: Event) -> None:
        if not self._replay_size:
            return
        buf = self._replay_buffer.setdefault(event.topic, deque(maxlen=self._replay_size))
        buf.append(event)

    @staticmethod
    def _dispatch_one(fn: Subscriber, event: Event) -> None:
        try:
            result = fn(event)
            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    asyncio.run(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Subscriber %s raised: %s", getattr(fn, '__name__', fn), exc)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def topics(self) -> list[str]:
        """Return sorted list of topics that have at least one subscriber."""
        return sorted(t for t, subs in self._subscribers.items() if subs)

    def subscriber_count(self, topic: str) -> int:
        """Return number of active subscribers for *topic*."""
        return len(self._subscribers.get(topic, []))

    def clear(self, topic: Optional[str] = None) -> None:
        """Remove all subscribers (and buffer) for *topic*, or everything if None."""
        if topic:
            self._subscribers.pop(topic, None)
            self._replay_buffer.pop(topic, None)
        else:
            self._subscribers.clear()
            self._replay_buffer.clear()
