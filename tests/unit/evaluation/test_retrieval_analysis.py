import csv

from scripts.benchmarks.analyze_retrieval_benchmark import analyze, jaccard, rank_biased_overlap


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def test_overlap_metrics():
    assert jaccard({"a", "b"}, {"b", "c"}) == 1 / 3
    assert rank_biased_overlap({"a": 1, "b": 2}, {"a": 1, "c": 2}) > 0
    assert rank_biased_overlap({}, {}) == 1.0


def test_analysis_collapses_chunks_to_papers_and_writes_reports(tmp_path):
    root = tmp_path / "benchmark"
    for method, rows in {
        "bm25": [
            {"question_number": "1", "question": "q", "rank": "1", "pmid": "p1", "chunk_id": "c1", "retrieval_method": "bm25", "retrieval_latency_ms": "10"},
            {"question_number": "1", "question": "q", "rank": "2", "pmid": "p1", "chunk_id": "c2", "retrieval_method": "bm25", "retrieval_latency_ms": "10"},
        ],
        "dense": [
            {"question_number": "1", "question": "q", "rank": "1", "pmid": "p1", "chunk_id": "c3", "retrieval_method": "dense", "retrieval_latency_ms": "20"},
            {"question_number": "1", "question": "q", "rank": "2", "pmid": "p2", "chunk_id": "c4", "retrieval_method": "dense", "retrieval_latency_ms": "20"},
        ],
    }.items():
        write_rows(root / method / "retrieved_chunks.csv", rows)

    output = analyze(root)
    summary = (output / "method_summary.csv").read_text(encoding="utf-8")
    specific = (output / "method_specific_papers.csv").read_text(encoding="utf-8")
    assert "unique_paper_count" in summary
    assert "p2" in specific
    assert (output / "benchmark_summary.md").exists()
