"""Measure retrieval latency and stability across repeated runs.

Corpus/model/retriever setup and one warm-up query are excluded from timed
measurements. Each benchmark question is then run three times per retriever.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_evidence_engine.corpus.loader import load_corpus
from scripts.benchmarks.run_retrieval_benchmark import BASELINE_QUESTIONS, build_retrievers


DEFAULT_METHODS = ["bm25", "dense", "hybrid_rrf", "hybrid_retriever"]
DEFAULT_WARMUP_QUERY = "EGFR osimertinib resistance"


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def pmid_ranking(documents: list[Any], top_k: int = 10) -> list[str]:
    """Return the first unique PMID for each result, capped at top_k papers."""
    pmids: list[str] = []
    seen: set[str] = set()
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        pmid = str(metadata.get("pmid", "")).strip()
        if pmid and pmid not in seen:
            seen.add(pmid)
            pmids.append(pmid)
        if len(pmids) == top_k:
            break
    return pmids


def jaccard(left: list[str] | set[str], right: list[str] | set[str]) -> float:
    left_set, right_set = set(left), set(right)
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else 1.0


def rbo_at_k(left: list[str], right: list[str], persistence: float = 0.9) -> float:
    """Calculate normalized finite-prefix RBO, where identical lists score 1."""
    if not 0 <= persistence < 1:
        raise ValueError("persistence must be in [0, 1)")
    depth_limit = max(len(left), len(right))
    if depth_limit == 0:
        return 1.0
    left_seen: set[str] = set()
    right_seen: set[str] = set()
    score = 0.0
    for depth in range(1, depth_limit + 1):
        if depth <= len(left):
            left_seen.add(left[depth - 1])
        if depth <= len(right):
            right_seen.add(right[depth - 1])
        overlap_at_depth = len(left_seen & right_seen) / depth
        score += (1 - persistence) * (persistence ** (depth - 1)) * overlap_at_depth
    normalization = 1 - persistence**depth_limit
    return score / normalization if normalization else 0.0


def positional_changes(left: list[str], right: list[str]) -> int:
    common = set(left) & set(right)
    left_positions = {pmid: index for index, pmid in enumerate(left, start=1)}
    right_positions = {pmid: index for index, pmid in enumerate(right, start=1)}
    return sum(left_positions[pmid] != right_positions[pmid] for pmid in common)


def run_stability_benchmark(
    output_dir: Path,
    methods: list[str] | None = None,
    questions: list[str] | None = None,
    runs: int = 3,
    top_k: int = 10,
    warmup_query: str = DEFAULT_WARMUP_QUERY,
    corpus_loader=load_corpus,
) -> Path:
    if runs < 2:
        raise ValueError("runs must be at least 2")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    selected_methods = methods or DEFAULT_METHODS
    unknown = set(selected_methods) - set(DEFAULT_METHODS)
    if unknown:
        raise ValueError(f"Unknown retriever methods: {sorted(unknown)}")
    benchmark_questions = questions or BASELINE_QUESTIONS

    faiss_db, bm25_index, documents = corpus_loader()
    all_retrievers = build_retrievers(faiss_db, bm25_index, documents, top_k)
    retrievers = {method: all_retrievers[method] for method in selected_methods}

    # Warm-up is intentionally outside all recorded timings.
    for retriever in retrievers.values():
        retriever.retrieve_docs(warmup_query)

    run_rows: list[dict[str, Any]] = []
    result_lists: dict[tuple[str, int, int], list[str]] = {}
    for method, retriever in retrievers.items():
        for question_number, question in enumerate(benchmark_questions, start=1):
            for run_number in range(1, runs + 1):
                started = time.perf_counter()
                documents_found = list(retriever.retrieve_docs(question))
                latency_ms = (time.perf_counter() - started) * 1000
                ranking = pmid_ranking(documents_found, top_k=top_k)
                result_lists[(method, question_number, run_number)] = ranking
                run_rows.append(
                    {
                        "question_number": question_number,
                        "question": question,
                        "retrieval_method": method,
                        "run_number": run_number,
                        "latency_ms": round(latency_ms, 2),
                        "retrieved_pmid_count": len(ranking),
                        "pmids": ";".join(ranking),
                    }
                )

    latency_by_question: list[dict[str, Any]] = []
    for method in selected_methods:
        for question_number, question in enumerate(benchmark_questions, start=1):
            values = [
                row["latency_ms"]
                for row in run_rows
                if row["retrieval_method"] == method and row["question_number"] == question_number
            ]
            latency_by_question.append(
                {
                    "question_number": question_number,
                    "question": question,
                    "retrieval_method": method,
                    "run_count": len(values),
                    "mean_latency_ms": round(statistics.mean(values), 2),
                    "std_latency_ms": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
                    "min_latency_ms": round(min(values), 2),
                    "max_latency_ms": round(max(values), 2),
                }
            )

    latency_overall: list[dict[str, Any]] = []
    for method in selected_methods:
        values = [row["latency_ms"] for row in run_rows if row["retrieval_method"] == method]
        latency_overall.append(
            {
                "retrieval_method": method,
                "question_count": len(benchmark_questions),
                "run_count": len(values),
                "mean_latency_ms": round(statistics.mean(values), 2),
                "std_latency_ms": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
                "min_latency_ms": round(min(values), 2),
                "max_latency_ms": round(max(values), 2),
            }
        )

    pairwise_rows: list[dict[str, Any]] = []
    stability_summary: list[dict[str, Any]] = []
    for method in selected_methods:
        for question_number, question in enumerate(benchmark_questions, start=1):
            comparisons = []
            for run_a, run_b in itertools.combinations(range(1, runs + 1), 2):
                left = result_lists[(method, question_number, run_a)]
                right = result_lists[(method, question_number, run_b)]
                left5, right5 = left[:5], right[:5]
                row = {
                    "question_number": question_number,
                    "question": question,
                    "retrieval_method": method,
                    "run_a": run_a,
                    "run_b": run_b,
                    "jaccard_at_10": round(jaccard(left, right), 6),
                    "jaccard_at_5": round(jaccard(left5, right5), 6),
                    "rbo_at_10": round(rbo_at_k(left, right), 6),
                    "top5_set_identical": left5 == right5 or set(left5) == set(right5),
                    "top5_order_identical": left5 == right5,
                    "ranking_order_changed": left != right,
                    "common_pmid_count": len(set(left) & set(right)),
                    "common_pmid_position_changes": positional_changes(left, right),
                }
                pairwise_rows.append(row)
                comparisons.append(row)
            stability_summary.append(
                {
                    "question_number": question_number,
                    "question": question,
                    "retrieval_method": method,
                    "comparison_count": len(comparisons),
                    "mean_jaccard_at_10": round(statistics.mean(r["jaccard_at_10"] for r in comparisons), 6),
                    "min_jaccard_at_10": round(min(r["jaccard_at_10"] for r in comparisons), 6),
                    "mean_jaccard_at_5": round(statistics.mean(r["jaccard_at_5"] for r in comparisons), 6),
                    "mean_rbo_at_10": round(statistics.mean(r["rbo_at_10"] for r in comparisons), 6),
                    "all_top5_sets_identical": all(r["top5_set_identical"] for r in comparisons),
                    "all_top5_orders_identical": all(r["top5_order_identical"] for r in comparisons),
                    "ranking_change_count": sum(r["ranking_order_changed"] for r in comparisons),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "run_results.csv", list(run_rows[0]), run_rows)
    write_csv(output_dir / "latency_by_question.csv", list(latency_by_question[0]), latency_by_question)
    write_csv(output_dir / "latency_overall.csv", list(latency_overall[0]), latency_overall)
    write_csv(output_dir / "stability_pairwise.csv", list(pairwise_rows[0]), pairwise_rows)
    write_csv(output_dir / "stability_summary.csv", list(stability_summary[0]), stability_summary)
    (output_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "methods": selected_methods,
                "question_count": len(benchmark_questions),
                "runs_per_question": runs,
                "top_k": top_k,
                "warmup_query": warmup_query,
                "latency_scope": "timed retrieve_docs call after setup and warm-up",
                "rbo_persistence": 0.9,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "stability_report.md").write_text(
        render_report(selected_methods, latency_overall, stability_summary), encoding="utf-8"
    )
    return output_dir


def render_report(methods: list[str], latency_overall: list[dict[str, Any]], stability_summary: list[dict[str, Any]]) -> str:
    lines = [
        "# Latency and Retrieval Stability Report",
        "",
        "Latency excludes corpus/model/retriever setup and the untimed warm-up query. Each question was run three times.",
        "",
        "## Overall latency",
        "",
        "| Method | Mean (ms) | Std dev (ms) | Min (ms) | Max (ms) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in latency_overall:
        lines.append(f"| {row['retrieval_method']} | {row['mean_latency_ms']} | {row['std_latency_ms']} | {row['min_latency_ms']} | {row['max_latency_ms']} |")
    lines += ["", "## Stability summary", "", "| Method | Question | Mean Jaccard@10 | Mean RBO@10 | Mean Jaccard@5 | Top-5 sets always identical | Top-5 orders always identical |", "|---|---:|---:|---:|---:|---|---|"]
    for row in stability_summary:
        lines.append(f"| {row['retrieval_method']} | {row['question_number']} | {row['mean_jaccard_at_10']} | {row['mean_rbo_at_10']} | {row['mean_jaccard_at_5']} | {row['all_top5_sets_identical']} | {row['all_top5_orders_identical']} |")
    lines += ["", "## Interpretation", "", "Jaccard@10 measures retrieved-set stability, while RBO@10 measures rank-sensitive stability. Neither metric measures relevance or retrieval quality. A stable but irrelevant ranking can still score highly.", ""]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retriever", action="append", dest="retrievers", choices=DEFAULT_METHODS)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--warmup-query", default=DEFAULT_WARMUP_QUERY)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = run_stability_benchmark(
        args.output_dir,
        methods=args.retrievers,
        runs=args.runs,
        top_k=args.top_k,
        warmup_query=args.warmup_query,
    )
    print(f"Saved latency/stability benchmark to: {output.resolve()}")


if __name__ == "__main__":
    main()
