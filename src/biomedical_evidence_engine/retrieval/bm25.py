"""Independent lexical retrieval backed by rank-bm25."""

from __future__ import annotations

import numpy as np

from .utils import normalize_top_k, validate_query


class BM25Retriever:
    def __init__(self, bm25_index, documents, top_k: int = 5):
        self.bm25_index = bm25_index
        self.documents = documents
        self.top_k = normalize_top_k(top_k)

    def retrieve_docs(self, query: str, top_k: int | None = None) -> list:
        query = validate_query(query)
        limit = self.top_k if top_k is None else normalize_top_k(top_k)
        if limit == 0:
            return []
        scores = np.asarray(self.bm25_index.get_scores(query.lower().split()))
        if len(scores) != len(self.documents):
            raise ValueError("BM25 score count does not match the number of documents")
        indices = np.argsort(-scores, kind="stable")[:limit]
        return [self.documents[int(index)] for index in indices]
