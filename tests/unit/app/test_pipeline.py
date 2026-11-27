from dataclasses import dataclass

from biomedical_evidence_engine.app import pipeline


@dataclass
class Document:
    page_content: str


class FakeChain:
    def __or__(self, _other):
        return self

    def invoke(self, _query):
        return "answer"


class FakeRetriever:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.__class__.instances.append(self)

    def retrieve_docs(self, _query):
        documents = [Document("one"), Document("two"), Document("three")]
        return documents[: self.kwargs["top_k"]]


def test_run_rag_forwards_top_k_to_hybrid_retriever(monkeypatch):
    FakeRetriever.instances.clear()
    monkeypatch.setattr(pipeline, "HybridRetriever", FakeRetriever)
    monkeypatch.setattr(pipeline, "RunnableParallel", lambda _steps: FakeChain())
    monkeypatch.setattr(pipeline, "ChatOpenAI", lambda **_kwargs: object())
    monkeypatch.setattr(pipeline, "StrOutputParser", lambda: object())

    answer, documents = pipeline.run_rag(
        query="question",
        faiss_db=object(),
        bm25_index=object(),
        documents=[],
        top_k=2,
    )

    assert answer == "answer"
    assert len(documents) == 2
    assert FakeRetriever.instances[0].kwargs["top_k"] == 2
