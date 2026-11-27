"""Evaluate PMID-level relevance judgments for the retrieval benchmark.

The five annotation CSVs are combined, deduplicated by question and PMID, and
evaluated against method-specific ranks. Precision/recall/MRR treat labels 1
and 2 as relevant; nDCG uses the original graded labels 0, 1, and 2.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


METHODS = {
    "bm25": "bm25_rank",
    "dense": "dense_rank",
    "hybrid_rrf": "hybrid_rrf_rank",
    "hybrid_retriever": "hybrid_retriever_rank",
}
LABEL_COLUMN = "relevance_label"
VALID_LABELS = {0, 1, 2}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_rank(value: str) -> float | None:
    try:
        rank = float(value)
    except (TypeError, ValueError):
        return None
    return rank if rank > 0 else None


def combine_judgments(annotation_paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in annotation_paths:
        rows.extend(read_csv(path))
    if not rows:
        raise ValueError("No annotation rows were found")

    required = {"question_number", "pmid", LABEL_COLUMN} | set(METHODS.values())
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"Annotation files are missing columns: {sorted(missing)}")

    # The annotation exporter normally already produces one row per PMID.
    # This defensive merge prevents duplicate PMID judgments from changing the
    # denominator or creating duplicate ranked results.
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("question_number", "").strip(), row.get("pmid", "").strip())].append(row)

    combined: list[dict[str, str]] = []
    for group in grouped.values():
        merged = dict(group[0])
        for method, rank_column in METHODS.items():
            ranks = [parse_rank(row.get(rank_column, "")) for row in group]
            ranks = [rank for rank in ranks if rank is not None]
            merged[rank_column] = str(int(min(ranks))) if ranks else ""
        labels = {row.get(LABEL_COLUMN, "").strip() for row in group if row.get(LABEL_COLUMN, "").strip()}
        merged[LABEL_COLUMN] = next(iter(labels)) if len(labels) == 1 else ("" if not labels else "CONFLICT")
        combined.append(merged)
    return sorted(combined, key=lambda row: (int(row["question_number"]), row["pmid"]))


def validate_labels(rows: list[dict[str, str]]) -> list[str]:
    errors = []
    for row in rows:
        label = row.get(LABEL_COLUMN, "").strip()
        if not label:
            errors.append(f"missing relevance label: Q{row['question_number']} PMID {row['pmid']}")
        elif label == "CONFLICT" or label not in {str(value) for value in VALID_LABELS}:
            errors.append(f"invalid relevance label '{label}': Q{row['question_number']} PMID {row['pmid']}")
    return errors


def ranked_pmids(rows: list[dict[str, str]], rank_column: str) -> list[tuple[str, int]]:
    ranked = []
    for row in rows:
        rank = parse_rank(row.get(rank_column, ""))
        if rank is not None:
            ranked.append((rank, row["pmid"]))
    ranked.sort(key=lambda item: (item[0], item[1]))
    # Re-rank after collapsing chunks to PMIDs. Raw chunk ranks may contain
    # gaps when several chunks from the same paper were retrieved.
    return [(pmid, paper_rank) for paper_rank, (_, pmid) in enumerate(ranked, start=1)]


def dcg(labels: list[int]) -> float:
    return sum((2**label - 1) / math.log2(index + 2) for index, label in enumerate(labels))


def calculate_metrics(rows: list[dict[str, str]], method: str) -> list[dict[str, Any]]:
    by_question: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_question[row["question_number"]].append(row)

    metric_rows: list[dict[str, Any]] = []
    rank_column = METHODS[method]
    for question_number in sorted(by_question, key=int):
        question_rows = by_question[question_number]
        labels = {row["pmid"]: int(row[LABEL_COLUMN]) for row in question_rows}
        relevant_pool = {pmid for pmid, label in labels.items() if label in {1, 2}}
        ranking = ranked_pmids(question_rows, rank_column)
        top5 = ranking[:5]
        relevant_top5 = [pmid for pmid, _ in top5 if labels[pmid] in {1, 2}]
        first_relevant_rank = next((rank for pmid, rank in ranking if labels[pmid] in {1, 2}), None)
        reciprocal_rank = 1 / first_relevant_rank if first_relevant_rank else 0.0

        retrieved_labels = [labels[pmid] for pmid, _ in top5]
        ideal_labels = sorted(labels.values(), reverse=True)[:5]
        ideal_dcg = dcg(ideal_labels)
        ndcg = dcg(retrieved_labels) / ideal_dcg if ideal_dcg else 0.0
        precision = len(relevant_top5) / len(top5) if top5 else 0.0
        pooled_recall = len(relevant_top5) / len(relevant_pool) if relevant_pool else 0.0
        false_positives = [pmid for pmid, _ in top5 if labels[pmid] == 0]
        relevant_below_5 = [pmid for pmid, rank in ranking if rank > 5 and labels[pmid] in {1, 2}]
        missed_relevant = sorted(relevant_pool - {pmid for pmid, _ in ranking})
        metric_rows.append(
            {
                "question_number": question_number,
                "question": question_rows[0].get("question", ""),
                "retrieval_method": method,
                "judged_pool_papers": len(labels),
                "pooled_relevant_papers": len(relevant_pool),
                "retrieved_papers": len(ranking),
                "precision_at_5": round(precision, 6),
                "pooled_recall_at_5": round(pooled_recall, 6),
                "first_relevant_rank": first_relevant_rank or "",
                "mrr": round(reciprocal_rank, 6),
                "ndcg_at_5": round(ndcg, 6),
                "false_positive_count_at_5": len(false_positives),
                "relevant_below_rank_5_count": len(relevant_below_5),
                "missed_relevant_count": len(missed_relevant),
            }
        )
    return metric_rows


def load_latencies(benchmark_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for method in METHODS:
        path = benchmark_dir / method / "question_summary.csv"
        if not path.exists():
            continue
        for row in read_csv(path):
            rows.append(
                {
                    "question_number": row["question_number"],
                    "retrieval_method": method,
                    "retrieval_latency_ms": float(row["retrieval_latency_ms"]),
                }
            )
    return rows


def evaluate(annotation_paths: list[Path], benchmark_dir: Path, output_dir: Path, allow_unjudged: bool = False) -> Path:
    rows = combine_judgments(annotation_paths)
    output_dir.mkdir(parents=True, exist_ok=True)
    combined_fields = list(rows[0])
    write_csv(output_dir / "relevance_judgments_v1.csv", combined_fields, rows)
    label_errors = validate_labels(rows)
    if label_errors and not allow_unjudged:
        raise ValueError(
            f"Cannot calculate metrics: {len(label_errors)} label errors. "
            "Annotate all rows first or use --allow-unjudged for structural export."
        )

    if label_errors:
        (output_dir / "label_validation_errors.txt").write_text("\n".join(label_errors) + "\n", encoding="utf-8")
        return output_dir

    question_metrics: list[dict[str, Any]] = []
    for method in METHODS:
        question_metrics.extend(calculate_metrics(rows, method))

    method_metrics = []
    for method in METHODS:
        method_rows = [row for row in question_metrics if row["retrieval_method"] == method]
        method_metrics.append(
            {
                "retrieval_method": method,
                "precision_at_5": round(statistics.mean(row["precision_at_5"] for row in method_rows), 6),
                "pooled_recall_at_5": round(statistics.mean(row["pooled_recall_at_5"] for row in method_rows), 6),
                "mrr": round(statistics.mean(row["mrr"] for row in method_rows), 6),
                "ndcg_at_5": round(statistics.mean(row["ndcg_at_5"] for row in method_rows), 6),
            }
        )

    latency_rows = load_latencies(benchmark_dir)
    latency_by_method: dict[str, list[float]] = defaultdict(list)
    for row in latency_rows:
        latency_by_method[row["retrieval_method"]].append(row["retrieval_latency_ms"])
    for row in method_metrics:
        values = latency_by_method.get(row["retrieval_method"], [])
        row["mean_latency_ms"] = round(statistics.mean(values), 2) if values else ""
        row["median_latency_ms"] = round(statistics.median(values), 2) if values else ""

    error_rows = build_error_analysis(rows)
    write_csv(output_dir / "question_metrics.csv", list(question_metrics[0]), question_metrics)
    write_csv(output_dir / "method_metrics.csv", list(method_metrics[0]), method_metrics)
    write_csv(output_dir / "latency_summary.csv", ["retrieval_method", "question_number", "retrieval_latency_ms"], latency_rows)
    write_csv(output_dir / "error_analysis.csv", list(error_rows[0]), error_rows)
    write_csv(output_dir / "top5_predictions.csv", list(build_top5_rows(rows)[0]), build_top5_rows(rows))
    (output_dir / "relevance_evaluation_report.md").write_text(
        render_report(method_metrics, question_metrics, error_rows), encoding="utf-8"
    )
    return output_dir


def build_top5_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result = []
    for method, rank_column in METHODS.items():
        by_question: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            by_question[row["question_number"]].append(row)
        for question_number, question_rows in by_question.items():
            labels = {row["pmid"]: int(row[LABEL_COLUMN]) for row in question_rows}
            for pmid, rank in ranked_pmids(question_rows, rank_column)[:5]:
                result.append(
                    {
                        "question_number": question_number,
                        "question": question_rows[0].get("question", ""),
                        "retrieval_method": method,
                        "rank": rank,
                        "pmid": pmid,
                        "relevance_label": labels[pmid],
                        "binary_relevant": int(labels[pmid] in {1, 2}),
                    }
                )
    return result


def build_error_analysis(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result = []
    for method, rank_column in METHODS.items():
        by_question: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            by_question[row["question_number"]].append(row)
        for question_number, question_rows in by_question.items():
            labels = {row["pmid"]: int(row[LABEL_COLUMN]) for row in question_rows}
            ranking = ranked_pmids(question_rows, rank_column)
            top5 = ranking[:5]
            for pmid, rank in top5:
                label = labels[pmid]
                if label == 0:
                    category = "false_positive_at_5"
                else:
                    category = "true_positive_at_5"
                result.append(
                    {
                        "question_number": question_number,
                        "question": question_rows[0].get("question", ""),
                        "retrieval_method": method,
                        "pmid": pmid,
                        "rank": rank,
                        "relevance_label": label,
                        "error_category": category,
                    }
                )
            for pmid, rank in ranking[5:]:
                if labels[pmid] in {1, 2}:
                    result.append(
                        {
                            "question_number": question_number,
                            "question": question_rows[0].get("question", ""),
                            "retrieval_method": method,
                            "pmid": pmid,
                            "rank": rank,
                            "relevance_label": labels[pmid],
                            "error_category": "relevant_below_5",
                        }
                    )
    return result


def render_report(method_metrics: list[dict[str, Any]], question_metrics: list[dict[str, Any]], error_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Relevance Evaluation Report",
        "",
        "Labels 1 and 2 count as relevant for Precision@5, pooled Recall@5, and MRR. nDCG@5 uses graded labels 0, 1, and 2.",
        "",
        "## Method comparison",
        "",
        "| Method | Precision@5 | Pooled Recall@5 | MRR | nDCG@5 | Mean latency (ms) | Median latency (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in method_metrics:
        lines.append(
            f"| {row['retrieval_method']} | {row['precision_at_5']:.4f} | {row['pooled_recall_at_5']:.4f} | "
            f"{row['mrr']:.4f} | {row['ndcg_at_5']:.4f} | {row['mean_latency_ms']} | {row['median_latency_ms']} |"
        )
    lines += ["", "## Methodological limitation", "", "Pooled Recall@5 is recall against the judged union of retrieved candidates, not recall against the full corpus. A relevant paper missed by every retrieval method cannot appear in this denominator.", "", "## Error analysis", ""]
    for category in ["false_positive_at_5", "relevant_below_5"]:
        lines.append(f"- `{category}`: {sum(row['error_category'] == category for row in error_rows)} results")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotation-dir", type=Path, required=True)
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--allow-unjudged", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    annotation_paths = [args.annotation_dir / f"question_{number:02d}_annotation.csv" for number in range(1, 6)]
    missing = [str(path) for path in annotation_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing annotation files: {missing}")
    output = evaluate(annotation_paths, args.benchmark_dir, args.output_dir, args.allow_unjudged)
    print(f"Saved relevance evaluation outputs to: {output.resolve()}")


if __name__ == "__main__":
    main()
