from dataclasses import dataclass

import pytest

from biomedical_evidence_engine.retrieval.bm25 import BM25Retriever
from biomedical_evidence_engine.retrieval.dense import DenseRetriever
from biomedical_evidence_engine.retrieval.hybrid_rrf import HybridRRF


@dataclass
class Document:
    chunk_id: str
    page_content: str = ""

    @property
    def metadata(self):
        return {"chunk_id": self.chunk_id}


class FakeBM25:
    def __init__(self, scores):
        self.scores = scores
        self.queries = []

    def get_scores(self, query):
        self.queries.append(query)
        return self.scores


class FakeFAISS:
    def __init__(self, documents):
        self.documents = documents
        self.calls = []

    def similarity_search(self, query, k):
        self.calls.append((query, k))
        return self.documents[:k]


def test_bm25_ranks_documents_and_tokenizes_query():
    documents = [Document("a"), Document("b"), Document("c")]
    index = FakeBM25([0.1, 2.0, 1.0])

    result = BM25Retriever(index, documents, top_k=2).retrieve_docs("EGFR T790M")

    assert [doc.chunk_id for doc in result] == ["b", "c"]
    assert index.queries == [["egfr", "t790m"]]


def test_dense_retriever_delegates_to_vector_store():
    documents = [Document("a"), Document("b")]
    store = FakeFAISS(documents)

    result = DenseRetriever(store, top_k=1).retrieve_docs("question")

    assert result == [documents[0]]
    assert store.calls == [("question", 1)]


def test_hybrid_rrf_fuses_and_deduplicates_without_reranking():
    dense = [Document("a"), Document("b")]
    lexical = [Document("b"), Document("c")]

    class StubRetriever:
        def __init__(self, docs):
            self.docs = docs

        def retrieve_docs(self, query, top_k=None):
            return self.docs

    retriever = HybridRRF(
        dense_retriever=StubRetriever(dense),
        bm25_retriever=StubRetriever(lexical),
        top_k=3,
        candidate_k=2,
    )

    result = retriever.retrieve_docs("question")

    assert [doc.chunk_id for doc in result] == ["b", "a", "c"]


def test_hybrid_rrf_supports_raw_corpus_components():
    documents = [Document("a"), Document("b")]
    result = HybridRRF(
        faiss_db=FakeFAISS([documents[1], documents[0]]),
        bm25_index=FakeBM25([2.0, 1.0]),
        documents=documents,
        top_k=1,
        candidate_k=2,
    ).retrieve_docs("query")

    assert [doc.chunk_id for doc in result] == ["b"]


@pytest.mark.parametrize("query", ["", "   "])
def test_hybrid_rrf_rejects_empty_queries(query):
    retriever = HybridRRF(
        dense_retriever=type("Stub", (), {"retrieve_docs": lambda self, query, top_k=None: []})(),
        bm25_retriever=type("Stub", (), {"retrieve_docs": lambda self, query, top_k=None: []})(),
    )

    with pytest.raises(ValueError, match="query must not be empty"):
        retriever.retrieve_docs(query)


def test_hybrid_rrf_rejects_documents_without_chunk_id():
    missing_id = type("Document", (), {"metadata": {}, "page_content": "text"})()

    class StubRetriever:
        def retrieve_docs(self, query, top_k=None):
            return [missing_id]

    retriever = HybridRRF(
        dense_retriever=StubRetriever(),
        bm25_retriever=StubRetriever(),
    )

    with pytest.raises(ValueError, match="missing required chunk_id"):
        retriever.retrieve_docs("question")


@pytest.mark.parametrize("bad_top_k", [-1, 1.5, True])
def test_invalid_top_k_is_rejected(bad_top_k):
    with pytest.raises((TypeError, ValueError)):
        DenseRetriever(FakeFAISS([]), top_k=bad_top_k)
