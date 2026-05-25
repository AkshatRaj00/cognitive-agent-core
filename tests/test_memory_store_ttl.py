"""
Regression tests for MemoryStore lazy TTL eviction fix.
Covers: Issue #10 - expired keys returned before sweeper runs.
"""
from __future__ import annotations

import time
import threading
import pytest

from core.memory_store_patch import MemoryStoreTTLFixed


def test_get_returns_none_after_ttl_expires():
    store = MemoryStoreTTLFixed(sweep_interval=9999)
    store.set("key", "value", ttl=0.05)  # 50ms TTL
    assert store.get("key") == "value"
    time.sleep(0.1)  # Wait for expiry
    assert store.get("key") is None  # Bug fix: should be None now


def test_get_returns_value_before_expiry():
    store = MemoryStoreTTLFixed()
    store.set("x", 42, ttl=10)
    assert store.get("x") == 42


def test_get_with_no_ttl_never_expires():
    store = MemoryStoreTTLFixed()
    store.set("persistent", "forever")
    time.sleep(0.05)
    assert store.get("persistent") == "forever"


def test_lazy_evict_removes_key_from_store():
    store = MemoryStoreTTLFixed(sweep_interval=9999)
    store.set("temp", "data", ttl=0.05)
    time.sleep(0.1)
    store.get("temp")  # Trigger lazy eviction
    # Key should be gone from internal store
    assert "temp" not in store._store


def test_exists_returns_false_for_expired_key():
    store = MemoryStoreTTLFixed(sweep_interval=9999)
    store.set("gone", True, ttl=0.05)
    time.sleep(0.1)
    assert not store.exists("gone")


def test_ttl_remaining_returns_zero_for_expired():
    store = MemoryStoreTTLFixed(sweep_interval=9999)
    store.set("k", 1, ttl=0.05)
    time.sleep(0.1)
    assert store.ttl_remaining("k") == 0.0


def test_len_excludes_expired_keys():
    store = MemoryStoreTTLFixed(sweep_interval=9999)
    store.set("a", 1, ttl=0.05)
    store.set("b", 2, ttl=100)
    assert len(store) == 2
    time.sleep(0.1)
    assert len(store) == 1


def test_thread_safety_concurrent_reads_writes():
    store = MemoryStoreTTLFixed()
    errors = []

    def writer():
        for i in range(50):
            store.set(f"key_{i}", i, ttl=0.5)

    def reader():
        for i in range(50):
            try:
                store.get(f"key_{i}")
            except Exception as e:
                errors.append(str(e))

    threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Thread safety errors: {errors}"
