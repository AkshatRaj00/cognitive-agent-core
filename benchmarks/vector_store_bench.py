"""
Benchmark: brute-force vs FAISS VectorStore.

Usage::
    python benchmarks/vector_store_bench.py --n 10000 --dim 384 --top-k 10
"""
from __future__ import annotations

import argparse
import time
import numpy as np


def run_benchmark(n: int, dim: int, top_k: int) -> None:
    from core.vector_store_faiss import VectorStoreFAISS

    print(f"\n=== VectorStore Benchmark ===")
    print(f"Vectors: {n:,} | Dim: {dim} | top_k: {top_k}\n")

    vectors = np.random.randn(n, dim).astype(np.float32)
    query = np.random.randn(dim).astype(np.float32)

    store = VectorStoreFAISS(dim=dim, metric="cosine")
    for i, v in enumerate(vectors):
        store.add(f"doc_{i}", v, {"idx": i})

    store.rebuild_index()

    # Warm up
    store.search(query, top_k=top_k)

    runs = 20
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        store.search(query, top_k=top_k)
        times.append((time.perf_counter() - t0) * 1000)

    avg = sum(times) / len(times)
    print(f"Average query time over {runs} runs: {avg:.2f}ms")
    print(f"Min: {min(times):.2f}ms | Max: {max(times):.2f}ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10_000)
    parser.add_argument("--dim", type=int, default=384)
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args()
    run_benchmark(args.n, args.dim, args.top_k)
