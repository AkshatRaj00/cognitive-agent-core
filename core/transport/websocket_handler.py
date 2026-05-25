"""
WebSocketHandler — real-time bidirectional streaming for AgentEngine.

Provides token-by-token streaming over WebSocket with:
- Auto-reconnect with exponential backoff
- Ping/pong heartbeat to detect stale connections
- Graceful disconnect handling
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import AsyncIterator, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class WSConfig:
    host: str = "0.0.0.0"
    port: int = 8765
    ping_interval: float = 20.0
    ping_timeout: float = 10.0
    max_reconnect_attempts: int = 5
    reconnect_base_delay: float = 1.0


@dataclass
class StreamChunk:
    token: str
    index: int
    finish_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps({
            "token": self.token,
            "index": self.index,
            "finish_reason": self.finish_reason,
            "timestamp": self.timestamp,
        })


class WebSocketHandler:
    """Handles WebSocket connections for streaming agent responses."""

    def __init__(self, config: Optional[WSConfig] = None) -> None:
        self.config = config or WSConfig()
        self._connections: dict[str, object] = {}
        self._on_message: Optional[Callable] = None

    def on_message(self, handler: Callable) -> Callable:
        """Decorator to register a message handler."""
        self._on_message = handler
        return handler

    async def send_stream(
        self,
        websocket: object,
        token_iter: AsyncIterator[str],
    ) -> None:
        """Stream tokens from an async iterator to a WebSocket client."""
        index = 0
        try:
            async for token in token_iter:
                chunk = StreamChunk(token=token, index=index)
                await websocket.send(chunk.to_json())  # type: ignore[attr-defined]
                index += 1
                logger.debug("Sent token %d: %r", index, token)

            # Send final finish chunk
            final = StreamChunk(token="", index=index, finish_reason="stop")
            await websocket.send(final.to_json())  # type: ignore[attr-defined]
            logger.info("Stream completed after %d tokens", index)

        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Stream error at token %d: %s", index, exc)
            error_msg = json.dumps({"error": str(exc), "index": index})
            try:
                await websocket.send(error_msg)  # type: ignore[attr-defined]
            except Exception:  # pylint: disable=broad-except
                pass

    async def _heartbeat(self, websocket: object, interval: float) -> None:
        """Send periodic pings to keep the connection alive."""
        while True:
            await asyncio.sleep(interval)
            try:
                await websocket.ping()  # type: ignore[attr-defined]
                logger.debug("Heartbeat ping sent")
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Heartbeat failed: %s", exc)
                break

    def reconnect_delay(self, attempt: int) -> float:
        """Exponential backoff delay for reconnect attempts."""
        delay = self.config.reconnect_base_delay * (2 ** attempt)
        logger.debug("Reconnect attempt %d — waiting %.1fs", attempt, delay)
        return delay

    async def connect_with_retry(self, uri: str) -> object:
        """Connect to a WebSocket URI with exponential backoff retry."""
        import websockets  # optional dependency

        for attempt in range(self.config.max_reconnect_attempts):
            try:
                ws = await websockets.connect(uri)  # type: ignore
                logger.info("Connected to %s on attempt %d", uri, attempt + 1)
                return ws
            except Exception as exc:  # pylint: disable=broad-except
                if attempt < self.config.max_reconnect_attempts - 1:
                    delay = self.reconnect_delay(attempt)
                    logger.warning("Connection failed (%s), retrying in %.1fs", exc, delay)
                    await asyncio.sleep(delay)
                else:
                    raise ConnectionError(
                        f"Failed to connect to {uri} after {self.config.max_reconnect_attempts} attempts"
                    ) from exc
        raise ConnectionError("Unreachable")
