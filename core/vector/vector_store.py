"""In-memory vector store with cosine similarity search."""
import math
from typing import Any, List, Optional, Tuple


class VectorStore:
    """Stores embedding vectors and supports similarity-based retrieval."""

    def __init__(self, dim: int = 768):
        self.dim = dim
        self._store: dict[str, dict] = {}

    def _norm(self, vec: List[float]) -> float:
        return math.sqrt(sum(v * v for v in vec))

    def _cosine(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        denom = self._norm(a) * self._norm(b)
        return dot / denom if denom else 0.0

    def upsert(self, doc_id: str, vector: List[float], metadata: Optional[dict] = None) -> None:
        if len(vector) != self.dim:
            raise ValueError(f"Expected dim {self.dim}, got {len(vector)}")
        self._store[doc_id] = {"vector": vector, "metadata": metadata or {}}

    def search(self, query: List[float], top_k: int = 5) -> List[Tuple[str, float, dict]]:
        scores = [
            (doc_id, self._cosine(query, entry["vector"]), entry["metadata"])
            for doc_id, entry in self._store.items()
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def delete(self, doc_id: str) -> bool:
        return bool(self._store.pop(doc_id, None))

    def count(self) -> int:
        return len(self._store)

    def reset(self) -> None:
        self._store.clear()
