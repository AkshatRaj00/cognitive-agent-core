"""rag package — Retrieval-Augmented Generation utilities."""

from .retriever import Document, RAGRetriever, RetrievalResult

__all__ = ["RAGRetriever", "Document", "RetrievalResult"]
