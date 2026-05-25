"""
FAISS-accelerated VectorStore.

Drops in as a replacement for the brute-force VectorStore.
Uses FAISS IVFFlat for large indexes (>10k vectors) and falls back
to IndexFlatIP when FAISS is not installed or the index is small.

Performance targets:
  10k  vectors -> ~1ms  query  (vs ~140ms brute force)
  100k vectors -> ~18ms query  (vs ~1800ms brute force)
"""
from __future__ import annotations

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Literal, Optional

logger = logging.getLogger(__name__)

METRIC = Literal["cosine", "dot", "l2"]
FAISS_THRESHOLD = 10_000  # Use IVF index above this count


@dataclass
class SearchResult:
    id: str
    score: float
    metadata: dict = field(default_factory=dict)


class VectorStoreFAISS:
    """
    FAISS-accelerated vector store with automatic index selection.

    Falls back to NumPy brute-force when:
    - faiss-cpu is not installed
    - Number of vectors < FAISS_THRESHOLD
    """

    def __init__(
        self,
        dim: int,
        metric: METRIC = "cosine",
        nlist: int = 100,
        nprobe: int = 32,
    ) -> None:
        self.dim = dim
        self.metric = metric
        self.nlist = nlist
        self.nprobe = nprobe

        self._ids: list[str] = []
        self._vectors: list[np.ndarray] = []
        self._metadata: dict[str, dict] = {}
        self._faiss_index = None
        self._faiss_available = self._check_faiss()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, id: str, vector: np.ndarray, metadata: Optional[dict] = None) -> None:
        """Add a vector to the store."""
        vec = self._normalise(vector)
        self._ids.append(id)
        self._vectors.append(vec)
        self._metadata[id] = metadata or {}
        self._faiss_index = None  # Invalidate index
        logger.debug("Added vector %r (total=%d)", id, len(self._ids))

    def search(
        self, query: np.ndarray, top_k: int = 5
    ) -> list[SearchResult]:
        """Return the top-k most similar vectors."""
        if not self._ids:
            return []

        q = self._normalise(query)

        if self._faiss_available and len(self._ids) >= FAISS_THRESHOLD:
            return self._faiss_search(q, top_k)
        return self._brute_force_search(q, top_k)

    def delete(self, id: str) -> bool:
        """Remove a vector by ID."""
        if id not in self._metadata:
            return False
        idx = self._ids.index(id)
        self._ids.pop(idx)
        self._vectors.pop(idx)
        del self._metadata[id]
        self._faiss_index = None
        return True

    def rebuild_index(self) -> None:
        """Force rebuild the FAISS index (useful after bulk adds)."""
        self._faiss_index = None
        if self._faiss_available and len(self._ids) >= FAISS_THRESHOLD:
            self._build_faiss_index()
            logger.info("FAISS index rebuilt with %d vectors", len(self._ids))

    def __len__(self) -> int:
        return len(self._ids)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalise(self, vec: np.ndarray) -> np.ndarray:
        """L2-normalise for cosine similarity via dot product."""
        v = vec.astype(np.float32)
        if self.metric == "cosine":
            norm = np.linalg.norm(v)
            if norm > 0:
                v = v / norm
        return v

    def _brute_force_search(self, query: np.ndarray, top_k: int) -> list[SearchResult]:
        matrix = np.stack(self._vectors)  # (N, D)
        scores = matrix @ query           # dot product (cosine after normalise)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(
                id=self._ids[i],
                score=float(scores[i]),
                metadata=self._metadata[self._ids[i]],
            )
            for i in top_indices
        ]

    def _build_faiss_index(self) -> None:
        import faiss  # type: ignore
        matrix = np.stack(self._vectors)
        quantizer = faiss.IndexFlatIP(self.dim)
        index = faiss.IndexIVFFlat(quantizer, self.dim, min(self.nlist, len(self._ids)))
        index.train(matrix)
        index.add(matrix)
        index.nprobe = self.nprobe
        self._faiss_index = index
        logger.info("Built FAISS IVFFlat index: nlist=%d nprobe=%d", self.nlist, self.nprobe)

    def _faiss_search(self, query: np.ndarray, top_k: int) -> list[SearchResult]:
        import faiss  # type: ignore
        if self._faiss_index is None:
            self._build_faiss_index()
        q = query.reshape(1, -1)
        scores, indices = self._faiss_index.search(q, min(top_k, len(self._ids)))
        return [
            SearchResult(
                id=self._ids[i],
                score=float(scores[0][rank]),
                metadata=self._metadata[self._ids[i]],
            )
            for rank, i in enumerate(indices[0])
            if i >= 0
        ]

    @staticmethod
    def _check_faiss() -> bool:
        try:
            import faiss  # noqa: F401
            return True
        except ImportError:
            logger.info("faiss-cpu not installed — using brute-force search")
            return False
