"""Independent dense retrieval backed by a vector store."""

from __future__ import annotations

from .utils import normalize_top_k, validate_query


class DenseRetriever:
    def __init__(self, faiss_db, top_k: int = 5):
        self.faiss_db = faiss_db
        self.top_k = normalize_top_k(top_k)

    def retrieve_docs(self, query: str, top_k: int | None = None) -> list:
        query = validate_query(query)
        limit = self.top_k if top_k is None else normalize_top_k(top_k)
        if limit == 0:
            return []
        return list(self.faiss_db.similarity_search(query, k=limit))
