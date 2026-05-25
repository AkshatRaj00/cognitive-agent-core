"""Unit tests for memory_store.MemoryStore."""

import time
import pytest
from memory_store import MemoryStore


def test_set_and_get_basic():
    store = MemoryStore()
    store.set("key", "value")
    assert store.get("key") == "value"


def test_get_missing_returns_default():
    store = MemoryStore()
    assert store.get("nonexistent") is None
    assert store.get("nonexistent", default="fallback") == "fallback"


def test_delete_existing_key():
    store = MemoryStore()
    store.set("k", 1)
    assert store.delete("k") is True
    assert store.get("k") is None


def test_delete_missing_key():
    store = MemoryStore()
    assert store.delete("ghost") is False


def test_ttl_expiry():
    store = MemoryStore()
    store.set("temp", "data", ttl=0.05)   # 50 ms TTL
    assert store.get("temp") == "data"
    time.sleep(0.1)
    assert store.get("temp") is None       # should have expired


def test_default_ttl():
    store = MemoryStore(default_ttl=0.05)
    store.set("a", 1)
    time.sleep(0.1)
    assert store.get("a") is None


def test_per_entry_ttl_overrides_default():
    store = MemoryStore(default_ttl=0.05)
    store.set("long", "lives", ttl=10.0)
    time.sleep(0.1)
    assert store.get("long") == "lives"   # per-entry TTL not yet expired


def test_exists():
    store = MemoryStore()
    store.set("x", 42)
    assert store.exists("x") is True
    assert store.exists("y") is False


def test_keys_excludes_expired():
    store = MemoryStore()
    store.set("permanent", 1)
    store.set("ephemeral", 2, ttl=0.05)
    time.sleep(0.1)
    assert "permanent" in store.keys()
    assert "ephemeral" not in store.keys()


def test_clear():
    store = MemoryStore()
    store.set("a", 1)
    store.set("b", 2)
    store.clear()
    assert len(store) == 0


def test_len():
    store = MemoryStore()
    assert len(store) == 0
    store.set("a", 1)
    store.set("b", 2)
    assert len(store) == 2
