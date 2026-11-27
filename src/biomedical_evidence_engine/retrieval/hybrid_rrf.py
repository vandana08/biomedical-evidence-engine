"""Hybrid reciprocal-rank fusion without cross-encoder reranking."""

from __future__ import annotations

from .bm25 import BM25Retriever
from .dense import DenseRetriever
from .utils import normalize_top_k, reciprocal_rank_fusion, validate_query


class HybridRRF:
    def __init__(self, dense_retriever=None, bm25_retriever=None, top_k=5,
                 candidate_k=None, rrf_k=60, *, faiss_db=None, bm25_index=None,
                 documents=None):
        self.top_k = normalize_top_k(top_k)
        self.candidate_k = normalize_top_k(candidate_k if candidate_k is not None else self.top_k * 2)
        if not isinstance(rrf_k, int) or isinstance(rrf_k, bool) or rrf_k < 0:
            raise ValueError("rrf_k must be a non-negative integer")
        self.rrf_k = rrf_k
        if dense_retriever is None:
            if faiss_db is None:
                raise ValueError("Provide dense_retriever or faiss_db")
            dense_retriever = DenseRetriever(faiss_db, self.candidate_k)
        if bm25_retriever is None:
            if bm25_index is None or documents is None:
                raise ValueError("Provide bm25_retriever or both bm25_index and documents")
            bm25_retriever = BM25Retriever(bm25_index, documents, self.candidate_k)
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever

    def retrieve_docs(self, query: str, top_k: int | None = None) -> list:
        query = validate_query(query)
        limit = self.top_k if top_k is None else normalize_top_k(top_k)
        if limit == 0:
            return []
        dense_docs = self.dense_retriever.retrieve_docs(query, top_k=self.candidate_k)
        bm25_docs = self.bm25_retriever.retrieve_docs(query, top_k=self.candidate_k)
        return reciprocal_rank_fusion([dense_docs, bm25_docs], self.rrf_k)[:limit]
