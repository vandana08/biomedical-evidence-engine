import csv
import json
from dataclasses import dataclass

from scripts.benchmarks.run_retrieval_benchmark import run_benchmark


@dataclass
class Document:
    pmid: str
    chunk_id: str

    @property
    def page_content(self):
        return f"document {self.pmid} chunk {self.chunk_id}"

    @property
    def metadata(self):
        return {"pmid": self.pmid, "chunk_id": self.chunk_id}


class FakeBM25:
    def get_scores(self, query):
        return [3.0, 2.0, 1.0]


class FakeFAISS:
    def similarity_search(self, query, k):
        return [Document("1", "c1"), Document("2", "c2"), Document("3", "c3")][:k]


def test_benchmark_writes_separate_method_outputs(tmp_path):
    documents = [Document("1", "c1"), Document("2", "c2"), Document("3", "c3")]

    def loader():
        return FakeFAISS(), FakeBM25(), documents

    output = run_benchmark(tmp_path / "benchmark", top_k=2, questions=["q"], corpus_loader=loader)

    methods = {"bm25", "dense", "hybrid_rrf", "hybrid_retriever"}
    assert {path.name for path in output.iterdir() if path.is_dir()} == methods
    for method in methods:
        chunk_path = output / method / "retrieved_chunks.csv"
        with chunk_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == 2
        assert {row["retrieval_method"] for row in rows} == {method}
        assert [row["rank"] for row in rows] == ["1", "2"]
        assert all(float(row["retrieval_latency_ms"]) >= 0 for row in rows)

        metadata = json.loads((output / method / "run_metadata.json").read_text())
        assert metadata["top_k"] == 2


def test_benchmark_rejects_invalid_top_k(tmp_path):
    try:
        run_benchmark(tmp_path / "benchmark", top_k=0, questions=["q"], corpus_loader=lambda: ())
    except ValueError as exc:
        assert "positive integer" in str(exc)
    else:
        raise AssertionError("Expected invalid top_k to be rejected")
