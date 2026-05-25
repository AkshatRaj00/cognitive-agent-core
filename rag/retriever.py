"""retriever.py — RAG retrieval layer with vector similarity search and chunking."""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Document:
    """A source document ingested into the retriever."""
    content: str
    source: str = ""
    doc_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.doc_id:
            self.doc_id = hashlib.sha1(self.content.encode()).hexdigest()[:12]


@dataclass
class Chunk:
    """A text chunk derived from a Document."""
    text: str
    doc_id: str
    chunk_index: int
    source: str = ""
    embedding: Optional[list[float]] = None


@dataclass
class RetrievalResult:
    """A retrieved chunk with its similarity score."""
    chunk: Chunk
    score: float

    @property
    def text(self) -> str:
        return self.chunk.text


# ---------------------------------------------------------------------------
# Chunker
# ---------------------------------------------------------------------------


class TextChunker:
    """Split documents into overlapping fixed-size token windows.

    Args:
        chunk_size:    Approximate number of words per chunk.
        overlap:       Number of words shared between adjacent chunks.
    """

    def __init__(self, chunk_size: int = 200, overlap: int = 40) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, doc: Document) -> list[Chunk]:
        words = doc.content.split()
        step = self.chunk_size - self.overlap
        chunks: list[Chunk] = []
        i = 0
        idx = 0
        while i < len(words):
            window = words[i : i + self.chunk_size]
            chunks.append(
                Chunk(
                    text=" ".join(window),
                    doc_id=doc.doc_id,
                    chunk_index=idx,
                    source=doc.source,
                )
            )
            i += step
            idx += 1
        return chunks


# ---------------------------------------------------------------------------
# Embedder (stub — replace with real model)
# ---------------------------------------------------------------------------


class BagOfWordsEmbedder:
    """Deterministic bag-of-words TF vector for zero-dependency retrieval.

    In production replace with:
    - ``sentence-transformers`` (local)
    - ``google.generativeai.embed_content`` (Gemini)
    - ``openai.embeddings.create``
    """

    def embed(self, text: str) -> list[float]:
        """Return a 64-dim unit-normalised BoW vector."""
        tokens = text.lower().split()
        vec = [0.0] * 64
        for tok in tokens:
            idx = abs(hash(tok)) % 64
            vec[idx] += 1.0
        return self._normalise(vec)

    @staticmethod
    def _normalise(vec: list[float]) -> list[float]:
        mag = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / mag for v in vec]


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


class RAGRetriever:
    """Retrieve the most relevant chunks for a query using cosine similarity.

    Example::

        retriever = RAGRetriever()
        retriever.ingest(Document(content="...", source="docs/overview.md"))
        results = retriever.retrieve("agent memory architecture", top_k=3)
        for r in results:
            print(r.score, r.text[:80])
    """

    def __init__(
        self,
        chunk_size: int = 200,
        overlap: int = 40,
        embedder: Optional[BagOfWordsEmbedder] = None,
    ) -> None:
        self._chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
        self._embedder = embedder or BagOfWordsEmbedder()
        self._chunks: list[Chunk] = []

    def ingest(self, doc: Document) -> int:
        """Chunk and embed a document. Returns number of chunks added."""
        new_chunks = self._chunker.chunk(doc)
        for chunk in new_chunks:
            chunk.embedding = self._embedder.embed(chunk.text)
        self._chunks.extend(new_chunks)
        logger.info("Ingested doc '%s': %d chunk(s)", doc.doc_id, len(new_chunks))
        return len(new_chunks)

    def ingest_many(self, docs: list[Document]) -> int:
        """Ingest multiple documents. Returns total chunks added."""
        return sum(self.ingest(d) for d in docs)

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        """Return the *top_k* most relevant chunks for *query*."""
        if not self._chunks:
            logger.warning("RAGRetriever has no ingested documents.")
            return []
        q_vec = self._embedder.embed(query)
        scored = [
            RetrievalResult(chunk=c, score=self._cosine(q_vec, c.embedding or []))
            for c in self._chunks
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))   # already unit-normalised

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def clear(self) -> None:
        self._chunks.clear()
