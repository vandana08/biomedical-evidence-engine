import numpy as np 

from src.reranker import CrossEncoderReranker



class HybridRetriever:
    def __init__(self, faiss_db, bm25_index, documents, top_k=5):
        self.faiss_db = faiss_db
        self.bm25_index = bm25_index
        self.documents = documents
        self.top_k = top_k
        self.reranker = CrossEncoderReranker()


    def reciprocal_rank_fusion(self, ranked_lists, k=60):
        scores = {}
        doc_lookup = {}

        for docs in ranked_lists:
            for rank, doc in enumerate(docs):
                doc_id = doc.metadata["pmid"]
                doc_lookup[doc_id] = doc

                scores.setdefault(doc_id, 0)
                scores[doc_id] += 1 / (k + rank + 1)

        ranked_doc_ids = sorted(scores, key=scores.get, reverse=True)
        return [doc_lookup[doc_id] for doc_id in ranked_doc_ids]

    def retrieve_docs(self, query):

        # Vector retrieval
        vector_docs = self.faiss_db.similarity_search(
            query, k=self.top_k * 2
        )

        # BM25 retrieval
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        bm25_top_idx = np.argsort(bm25_scores)[::-1][: self.top_k * 2]
        bm25_docs = [self.documents[i] for i in bm25_top_idx]

        # Fusion
        fused_docs = self.reciprocal_rank_fusion(
            [vector_docs, bm25_docs]
        )

        # Reranking step
        reranked_docs = self.reranker.rerank(
            query,
            fused_docs,
            top_k=self.top_k
        )

        return reranked_docs

