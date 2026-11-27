"""Benchmark the four retrieval strategies on the five baseline questions.

Run from the repository root:

    python run_retrieval_benchmark.py

The corpus is loaded once and each method is evaluated independently. Results
are written under ``outputs/retrieval_benchmark_<timestamp>/``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_evidence_engine.config.questions import BASELINE_QUESTIONS
from biomedical_evidence_engine.corpus.loader import load_corpus
from biomedical_evidence_engine.retrieval.bm25 import BM25Retriever
from biomedical_evidence_engine.retrieval.dense import DenseRetriever
from biomedical_evidence_engine.retrieval.hybrid_rrf import HybridRRF

CHUNK_FIELDS = [
    "question_number",
    "question",
    "rank",
    "pmid",
    "chunk_id",
    "retrieval_method",
    "retrieval_latency_ms",
]
SUMMARY_FIELDS = [
    "question_number",
    "question",
    "retrieval_method",
    "retrieved_chunk_count",
    "retrieval_latency_ms",
]


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def document_fields(document: Any) -> tuple[str, str]:
    metadata = getattr(document, "metadata", {}) or {}
    pmid = str(metadata.get("pmid", "")).strip()
    chunk_id = metadata.get("chunk_id", "")
    return pmid, "" if chunk_id is None else str(chunk_id)


def build_retrievers(faiss_db: Any, bm25_index: Any, documents: list, top_k: int):
    """Build all four strategies with a common final result size."""
    # Keep the independent benchmark components importable without loading the
    # optional cross-encoder dependency until the legacy method is constructed.
    from biomedical_evidence_engine.retrieval.hybrid_reranked import HybridRetriever

    return {
        "bm25": BM25Retriever(bm25_index, documents, top_k=top_k),
        "dense": DenseRetriever(faiss_db, top_k=top_k),
        "hybrid_rrf": HybridRRF(
            faiss_db=faiss_db,
            bm25_index=bm25_index,
            documents=documents,
            top_k=top_k,
            candidate_k=top_k * 2,
        ),
        "hybrid_retriever": HybridRetriever(
            faiss_db=faiss_db,
            bm25_index=bm25_index,
            documents=documents,
            top_k=top_k,
        ),
    }


def run_method(retriever: Any, question: str, top_k: int) -> tuple[list, float]:
    started = time.perf_counter()
    documents = list(retriever.retrieve_docs(question))[:top_k]
    latency_ms = (time.perf_counter() - started) * 1000
    return documents, round(latency_ms, 2)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_benchmark(
    output_root: Path,
    top_k: int = 10,
    questions: list[str] | None = None,
    corpus_loader: Callable[[], tuple[Any, Any, list]] = load_corpus,
) -> Path:
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")

    benchmark_questions = BASELINE_QUESTIONS if questions is None else questions
    if not benchmark_questions:
        raise ValueError("At least one benchmark question is required")

    faiss_db, bm25_index, documents = corpus_loader()
    retrievers = build_retrievers(faiss_db, bm25_index, documents, top_k)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    output_root.mkdir(parents=True, exist_ok=True)
    for method_name, retriever in retrievers.items():
        method_dir = output_root / method_name
        method_dir.mkdir(parents=True, exist_ok=True)
        chunk_rows: list[dict[str, Any]] = []
        summary_rows: list[dict[str, Any]] = []

        for question_number, question in enumerate(benchmark_questions, start=1):
            retrieved, latency_ms = run_method(retriever, question, top_k)
            summary_rows.append(
                {
                    "question_number": question_number,
                    "question": question,
                    "retrieval_method": method_name,
                    "retrieved_chunk_count": len(retrieved),
                    "retrieval_latency_ms": latency_ms,
                }
            )
            for rank, document in enumerate(retrieved, start=1):
                pmid, chunk_id = document_fields(document)
                chunk_rows.append(
                    {
                        "question_number": question_number,
                        "question": question,
                        "rank": rank,
                        "pmid": pmid,
                        "chunk_id": chunk_id,
                        "retrieval_method": method_name,
                        "retrieval_latency_ms": latency_ms,
                    }
                )

        write_csv(method_dir / "retrieved_chunks.csv", CHUNK_FIELDS, chunk_rows)
        write_csv(method_dir / "question_summary.csv", SUMMARY_FIELDS, summary_rows)
        (method_dir / "run_metadata.json").write_text(
            json.dumps(
                {
                    "run_timestamp_utc": run_timestamp,
                    "retrieval_method": method_name,
                    "question_count": len(benchmark_questions),
                    "top_k": top_k,
                    "corpus_path": "data/corpus_v1",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    (output_root / "run_metadata.json").write_text(
        json.dumps(
            {
                "run_timestamp_utc": run_timestamp,
                "question_count": len(benchmark_questions),
                "retrieval_methods": list(retrievers),
                "top_k": top_k,
                "corpus_path": "data/corpus_v1",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return output_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory; defaults to outputs/retrieval_benchmark_<timestamp>",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("outputs") / f"retrieval_benchmark_{stamp}"
    else:
        output_dir = args.output_dir
    saved_to = run_benchmark(output_dir, top_k=args.top_k)
    print(f"Saved retrieval benchmark outputs to: {saved_to.resolve()}")


if __name__ == "__main__":
    main()
