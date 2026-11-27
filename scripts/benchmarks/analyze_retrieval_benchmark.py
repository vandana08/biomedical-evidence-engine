"""Analyze agreement and differences in a retrieval benchmark run.

Run from the repository root:

    python analyze_retrieval_benchmark.py \
        --input-dir outputs/retrieval_benchmark_<timestamp>

If ``--input-dir`` is omitted, the newest ``outputs/retrieval_benchmark_*``
directory is analyzed. The report compares both chunk IDs and PMID-level
paper identities because one paper can contribute multiple chunks.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_METHODS = ["bm25", "dense", "hybrid_rrf", "hybrid_retriever"]
SHARED_FIELDS = ["question_number", "question", "pmid", "method_count", "methods"]
SPECIFIC_FIELDS = SHARED_FIELDS + ["retrieval_method"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def latest_benchmark_dir(outputs_dir: Path) -> Path:
    candidates = [
        path
        for path in outputs_dir.glob("retrieval_benchmark_*")
        if path.is_dir()
    ]
    if not candidates:
        raise FileNotFoundError(
            f"No retrieval_benchmark_* directories found under {outputs_dir}"
        )
    return max(candidates, key=lambda path: path.stat().st_mtime)


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def first_paper_ranks(rows: list[dict[str, str]]) -> dict[str, int]:
    ranks: dict[str, int] = {}
    for row in rows:
        pmid = row.get("pmid", "").strip()
        if pmid and pmid not in ranks:
            ranks[pmid] = int(row["rank"])
    return ranks


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def rank_biased_overlap(
    left_ranks: dict[str, int], right_ranks: dict[str, int], persistence: float = 0.9
) -> float:
    """Finite-list RBO using the union of the two ranked paper lists."""
    max_depth = max(left_ranks.values(), default=0)
    max_depth = max(max_depth, max(right_ranks.values(), default=0))
    if max_depth == 0:
        return 1.0
    left_seen: set[str] = set()
    right_seen: set[str] = set()
    score = 0.0
    for depth in range(1, max_depth + 1):
        left_seen.update(pmid for pmid, rank in left_ranks.items() if rank == depth)
        right_seen.update(pmid for pmid, rank in right_ranks.items() if rank == depth)
        overlap = len(left_seen & right_seen) / depth
        score += (1 - persistence) * (persistence ** (depth - 1)) * overlap
    return score


def load_benchmark(input_dir: Path) -> tuple[dict[str, dict[int, list[dict[str, str]]]], list[str]]:
    methods = [
        path.name
        for path in sorted(input_dir.iterdir())
        if path.is_dir() and (path / "retrieved_chunks.csv").exists()
    ]
    if not methods:
        raise FileNotFoundError(f"No method result directories found in {input_dir}")

    results: dict[str, dict[int, list[dict[str, str]]]] = {}
    for method in methods:
        grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
        for row in read_csv(input_dir / method / "retrieved_chunks.csv"):
            grouped[int(row["question_number"])].append(row)
        results[method] = dict(grouped)
    return results, methods


def analyze(input_dir: Path, output_dir: Path | None = None) -> Path:
    results, methods = load_benchmark(input_dir)
    output_dir = output_dir or input_dir / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    question_numbers = sorted(
        {question_number for method in methods for question_number in results[method]}
    )
    method_summary: list[dict[str, Any]] = []
    question_summary: list[dict[str, Any]] = []
    pairwise_rows: list[dict[str, Any]] = []
    rank_rows: list[dict[str, Any]] = []
    shared_rows: list[dict[str, Any]] = []
    specific_rows: list[dict[str, Any]] = []

    for method in methods:
        all_rows = [row for rows in results[method].values() for row in rows]
        latencies = [parse_float(row.get("retrieval_latency_ms")) for row in all_rows]
        unique_papers = {
            row["pmid"].strip() for row in all_rows if row.get("pmid", "").strip()
        }
        unique_chunks = {
            row["chunk_id"].strip()
            for row in all_rows
            if row.get("chunk_id", "").strip()
        }
        method_summary.append(
            {
                "retrieval_method": method,
                "question_count": len(results[method]),
                "chunk_count": len(all_rows),
                "unique_chunk_count": len(unique_chunks),
                "unique_paper_count": len(unique_papers),
                "mean_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
                "median_latency_ms": round(statistics.median(latencies), 2) if latencies else 0,
                "p95_latency_ms": round(percentile(latencies, 95), 2) if latencies else 0,
                "missing_pmid_count": sum(not row.get("pmid", "").strip() for row in all_rows),
                "missing_chunk_id_count": sum(not row.get("chunk_id", "").strip() for row in all_rows),
            }
        )

    for question_number in question_numbers:
        question_text = next(
            (
                rows[0].get("question", "")
                for method in methods
                for rows in [results[method].get(question_number, [])]
                if rows
            ),
            "",
        )
        paper_sets: dict[str, set[str]] = {}
        chunk_sets: dict[str, set[str]] = {}
        paper_ranks: dict[str, dict[str, int]] = {}
        for method in methods:
            rows = results[method].get(question_number, [])
            paper_sets[method] = {row["pmid"].strip() for row in rows if row.get("pmid", "").strip()}
            chunk_sets[method] = {row["chunk_id"].strip() for row in rows if row.get("chunk_id", "").strip()}
            paper_ranks[method] = first_paper_ranks(rows)
            latencies = [parse_float(row.get("retrieval_latency_ms")) for row in rows]
            question_summary.append(
                {
                    "question_number": question_number,
                    "question": question_text,
                    "retrieval_method": method,
                    "chunk_count": len(rows),
                    "unique_chunk_count": len(chunk_sets[method]),
                    "unique_paper_count": len(paper_sets[method]),
                    "retrieval_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0,
                }
            )

        all_papers: set[str] = set().union(*paper_sets.values()) if paper_sets else set()
        for pmid in sorted(all_papers):
            present = [method for method in methods if pmid in paper_sets[method]]
            row = {
                "question_number": question_number,
                "question": question_text,
                "pmid": pmid,
                "method_count": len(present),
                "methods": ";".join(present),
            }
            shared_rows.append(row)
            if len(present) == 1:
                specific_rows.append({**row, "retrieval_method": present[0]})

        for method_a, method_b in itertools.combinations(methods, 2):
            shared = paper_sets[method_a] & paper_sets[method_b]
            shared_ranks = [
                abs(paper_ranks[method_a][pmid] - paper_ranks[method_b][pmid])
                for pmid in shared
            ]
            pairwise_rows.append(
                {
                    "question_number": question_number,
                    "question": question_text,
                    "method_a": method_a,
                    "method_b": method_b,
                    "chunk_overlap_count": len(chunk_sets[method_a] & chunk_sets[method_b]),
                    "chunk_jaccard": round(jaccard(chunk_sets[method_a], chunk_sets[method_b]), 4),
                    "paper_overlap_count": len(shared),
                    "paper_jaccard": round(jaccard(paper_sets[method_a], paper_sets[method_b]), 4),
                    "shared_paper_rank_mae": round(statistics.mean(shared_ranks), 2) if shared_ranks else "",
                    "paper_rbo": round(rank_biased_overlap(paper_ranks[method_a], paper_ranks[method_b]), 4),
                }
            )
            rank_rows.append(pairwise_rows[-1].copy())

    write_csv(output_dir / "method_summary.csv", list(method_summary[0]), method_summary)
    write_csv(output_dir / "question_summary.csv", list(question_summary[0]), question_summary)
    write_csv(output_dir / "pairwise_overlap.csv", list(pairwise_rows[0]), pairwise_rows)
    write_csv(output_dir / "rank_agreement.csv", list(rank_rows[0]), rank_rows)
    write_csv(output_dir / "shared_papers.csv", SHARED_FIELDS, shared_rows)
    write_csv(output_dir / "method_specific_papers.csv", SPECIFIC_FIELDS, specific_rows)
    (output_dir / "benchmark_summary.md").write_text(
        render_markdown(input_dir, methods, method_summary, question_summary, pairwise_rows, shared_rows, specific_rows),
        encoding="utf-8",
    )
    return output_dir


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def render_markdown(
    input_dir: Path,
    methods: list[str],
    method_summary: list[dict[str, Any]],
    question_summary: list[dict[str, Any]],
    pairwise_rows: list[dict[str, Any]],
    shared_rows: list[dict[str, Any]],
    specific_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# Retrieval Benchmark Summary",
        "",
        f"- Input run: `{input_dir}`",
        f"- Methods: {', '.join(methods)}",
        "- Paper identity: PMID; chunk identity: chunk ID",
        "",
        "## Method summary",
        "",
        "| Method | Questions | Chunks | Unique papers | Mean latency (ms) | Median latency (ms) | P95 latency (ms) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in method_summary:
        lines.append(
            f"| {row['retrieval_method']} | {row['question_count']} | {row['chunk_count']} | "
            f"{row['unique_paper_count']} | {row['mean_latency_ms']} | {row['median_latency_ms']} | {row['p95_latency_ms']} |"
        )

    lines += ["", "## Pairwise paper-level agreement", "", "| Question | Method A | Method B | Paper overlap | Paper Jaccard | Paper RBO | Rank MAE |", "|---:|---|---|---:|---:|---:|---:|"]
    for row in pairwise_rows:
        lines.append(
            f"| {row['question_number']} | {row['method_a']} | {row['method_b']} | {row['paper_overlap_count']} | "
            f"{row['paper_jaccard']} | {row['paper_rbo']} | {row['shared_paper_rank_mae']} |"
        )

    lines += ["", "## Interpretation", ""]
    if pairwise_rows:
        mean_jaccard = statistics.mean(row["paper_jaccard"] for row in pairwise_rows)
        lines.append(
            f"Across all question/method pairs, mean paper-level Jaccard similarity was **{mean_jaccard:.3f}**. "
            "Lower values indicate that methods surfaced more method-specific papers."
        )
    lines.append(
        f"The run contains **{len(shared_rows)}** unique question-paper memberships, of which "
        f"**{len(specific_rows)}** were unique to one retrieval method."
    )
    lines.append(
        "These are retrieval-agreement findings, not relevance or biomedical-quality judgments; relevance assessment requires labeled evidence or expert review."
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir or latest_benchmark_dir(Path("outputs"))
    output_dir = analyze(input_dir, args.output_dir)
    print(f"Saved retrieval analysis to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
