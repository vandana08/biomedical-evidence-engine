from biomedical_evidence_engine.retrieval import reranker
from biomedical_evidence_engine.retrieval import hybrid_reranked


def test_cross_encoder_reranker_is_cached_per_model(monkeypatch):
    calls = []

    class FakeReranker:
        def __init__(self, model_name):
            calls.append(model_name)

    monkeypatch.setattr(reranker, "CrossEncoderReranker", FakeReranker)
    reranker.get_cross_encoder_reranker.cache_clear()

    try:
        first = reranker.get_cross_encoder_reranker("model-a")
        second = reranker.get_cross_encoder_reranker("model-a")
        third = reranker.get_cross_encoder_reranker("model-b")

        assert first is second
        assert first is not third
        assert calls == ["model-a", "model-b"]
    finally:
        reranker.get_cross_encoder_reranker.cache_clear()


def test_hybrid_retriever_accepts_injected_reranker(monkeypatch):
    supplied = object()

    def fail_if_called():
        raise AssertionError("cached reranker should not be requested")

    monkeypatch.setattr(hybrid_reranked, "get_cross_encoder_reranker", fail_if_called)

    retriever = hybrid_reranked.HybridRetriever(
        faiss_db=object(),
        bm25_index=object(),
        documents=[],
        reranker=supplied,
    )

    assert retriever.reranker is supplied


def test_hybrid_retrievers_share_cached_reranker(monkeypatch):
    calls = []

    class FakeReranker:
        def __init__(self, model_name):
            calls.append(model_name)

    monkeypatch.setattr(reranker, "CrossEncoderReranker", FakeReranker)
    reranker.get_cross_encoder_reranker.cache_clear()

    try:
        first = hybrid_reranked.HybridRetriever(object(), object(), [])
        second = hybrid_reranked.HybridRetriever(object(), object(), [])

        assert first.reranker is second.reranker
        assert calls == [reranker.DEFAULT_MODEL_NAME]
    finally:
        reranker.get_cross_encoder_reranker.cache_clear()
