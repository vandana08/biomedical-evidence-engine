"""Cross-encoder reranking."""

class CrossEncoderReranker:
    def __init__(self, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for CrossEncoder reranking."
            ) from exc
        self.model = CrossEncoder(model_name)

    def rerank(self, query, docs, top_k=5):
        pairs = [(query, doc.page_content) for doc in docs]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(docs, scores), key=lambda item: item[1], reverse=True)
        return [doc for doc, _ in ranked[:top_k]]
