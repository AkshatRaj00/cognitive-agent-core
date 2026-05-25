"""
Unit tests for WebSocketHandler.
"""
from __future__ import annotations

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.transport.websocket_handler import WebSocketHandler, WSConfig, StreamChunk


class FakeWebSocket:
    def __init__(self):
        self.sent: list[str] = []
        self.ping = AsyncMock()

    async def send(self, data: str) -> None:
        self.sent.append(data)


async def token_generator(tokens):
    for t in tokens:
        yield t


@pytest.mark.asyncio
async def test_send_stream_sends_all_tokens():
    handler = WebSocketHandler()
    ws = FakeWebSocket()
    tokens = ["Hello", " ", "world", "!"]
    await handler.send_stream(ws, token_generator(tokens))

    # 4 tokens + 1 final finish chunk
    assert len(ws.sent) == 5

    for i, raw in enumerate(ws.sent[:-1]):
        chunk = json.loads(raw)
        assert chunk["token"] == tokens[i]
        assert chunk["index"] == i
        assert chunk["finish_reason"] is None

    final = json.loads(ws.sent[-1])
    assert final["finish_reason"] == "stop"
    assert final["token"] == ""


@pytest.mark.asyncio
async def test_send_stream_sends_error_on_exception():
    handler = WebSocketHandler()
    ws = FakeWebSocket()

    async def bad_generator():
        yield "ok"
        raise RuntimeError("LLM failure")

    await handler.send_stream(ws, bad_generator())
    last = json.loads(ws.sent[-1])
    assert "error" in last
    assert "LLM failure" in last["error"]


def test_reconnect_delay_exponential():
    handler = WebSocketHandler(WSConfig(reconnect_base_delay=1.0))
    assert handler.reconnect_delay(0) == 1.0
    assert handler.reconnect_delay(1) == 2.0
    assert handler.reconnect_delay(2) == 4.0
    assert handler.reconnect_delay(3) == 8.0


def test_stream_chunk_to_json():
    chunk = StreamChunk(token="hi", index=3, finish_reason=None)
    data = json.loads(chunk.to_json())
    assert data["token"] == "hi"
    assert data["index"] == 3
    assert data["finish_reason"] is None
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_on_message_decorator():
    handler = WebSocketHandler()

    @handler.on_message
    async def my_handler(msg):
        return msg.upper()

    assert handler._on_message is my_handler
