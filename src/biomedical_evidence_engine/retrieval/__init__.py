"""Retrieval implementations with lazy optional imports."""

__all__ = ["BM25Retriever", "DenseRetriever", "HybridRRF", "HybridRetriever"]


def __getattr__(name):
    modules = {
        "BM25Retriever": ".bm25",
        "DenseRetriever": ".dense",
        "HybridRRF": ".hybrid_rrf",
        "HybridRetriever": ".hybrid_reranked",
    }
    if name in modules:
        from importlib import import_module
        return getattr(import_module(modules[name], __name__), name)
    raise AttributeError(name)
