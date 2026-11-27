"""Legacy FAISS + BM25 fusion followed by CrossEncoder reranking."""

import numpy as np

from .reranker import get_cross_encoder_reranker
from .utils import document_key


class HybridRetriever:
    def __init__(self, faiss_db, bm25_index, documents, top_k=5, reranker=None):
        self.faiss_db = faiss_db
        self.bm25_index = bm25_index
        self.documents = documents
        self.top_k = top_k
        self.reranker = reranker if reranker is not None else get_cross_encoder_reranker()

    def reciprocal_rank_fusion(self, ranked_lists, k=60):
        scores = {}
        doc_lookup = {}
        for docs in ranked_lists:
            for rank, doc in enumerate(docs):
                doc_id = document_key(doc)
                doc_lookup[doc_id] = doc
                scores.setdefault(doc_id, 0)
                scores[doc_id] += 1 / (k + rank + 1)
        ranked_doc_ids = sorted(scores, key=scores.get, reverse=True)
        return [doc_lookup[doc_id] for doc_id in ranked_doc_ids]

    def retrieve_docs(self, query):
        vector_docs = self.faiss_db.similarity_search(query, k=self.top_k * 2)
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        bm25_top_idx = np.argsort(bm25_scores)[::-1][: self.top_k * 2]
        bm25_docs = [self.documents[i] for i in bm25_top_idx]
        fused_docs = self.reciprocal_rank_fusion([vector_docs, bm25_docs])
        return self.reranker.rerank(query, fused_docs, top_k=self.top_k)
