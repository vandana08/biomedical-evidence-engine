import csv


from scripts.benchmarks.evaluate_relevance_judgments import calculate_metrics


def row(pmid, label, **ranks):
    values = {"question_number": "1", "question": "q", "pmid": pmid, "relevance_label": str(label)}
    values.update({f"{method}_rank": str(rank) for method, rank in ranks.items()})
    values.update({f"{method}_rank": "" for method in ["bm25", "dense", "hybrid_rrf", "hybrid_retriever"] if f"{method}_rank" not in values})
    return values


def test_metrics_use_binary_and_graded_relevance_correctly():
    rows = [
        row("p1", 2, bm25=1),
        row("p2", 1, bm25=2),
        row("p3", 0, bm25=3),
        row("p4", 2, bm25=6),
        row("p5", 0, bm25=4),
    ]
    result = calculate_metrics(rows, "bm25")[0]
    assert result["precision_at_5"] == 0.6
    assert result["pooled_recall_at_5"] == 1.0
    assert result["mrr"] == 1.0
    assert result["ndcg_at_5"] > 0
    assert result["relevant_below_rank_5_count"] == 0
