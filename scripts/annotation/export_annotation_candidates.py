"""Enrich a retrieval relevance pool with corpus abstracts for annotation.

The relevance pool is the authoritative candidate list. It is left-joined to
the corpus by PMID, so missing abstracts never remove candidate papers.
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_POOL_COLUMNS = {"question_number", "pmid"}
ANNOTATION_FIELDS = ["relevance_label", "justification"]
OUTPUT_FIELDS = ["question_number", "pmid", "chunk_id", "abstract_text"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def reconstruct_abstract(document: Any) -> tuple[str, str]:
    metadata = getattr(document, "metadata", {}) or {}
    sections = metadata.get("abstract_sections")
    if sections:
        rendered: list[str] = []
        for section in sections:
            text = str(section.get("text", "")).strip()
            if not text:
                continue
            label = section.get("label") or section.get("nlm_category")
            rendered.append(f"{label}: {text}" if label else text)
        abstract = "\n".join(rendered).strip()
        if abstract:
            return abstract, "abstract_sections"

    page_content = str(getattr(document, "page_content", "") or "").strip()
    if page_content:
        return page_content, "chunk_page_content_fallback"
    return "", "missing"


def build_abstract_lookup(documents: list[Any]) -> tuple[dict[str, dict[str, str]], int]:
    """Build one full-abstract record per PMID, preferring structured metadata."""
    candidates: dict[str, list[dict[str, str]]] = defaultdict(list)
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        pmid = str(metadata.get("pmid", "")).strip()
        if not pmid:
            continue
        abstract_text, abstract_source = reconstruct_abstract(document)
        candidates[pmid].append(
            {
                "abstract_text": abstract_text,
                "abstract_source": abstract_source,
                "title": str(metadata.get("title", "") or ""),
                "journal": str(metadata.get("journal", "") or ""),
                "year": str(metadata.get("year", "") or ""),
            }
        )

    lookup: dict[str, dict[str, str]] = {}
    conflict_count = 0
    for pmid, records in candidates.items():
        nonempty = [record for record in records if record["abstract_text"]]
        selected = max(nonempty or records, key=lambda record: len(record["abstract_text"]))
        distinct_texts = {record["abstract_text"] for record in nonempty}
        if len(distinct_texts) > 1:
            conflict_count += 1
        lookup[pmid] = selected
    return lookup, conflict_count


def merge_values(column: str, values: list[str]) -> str:
    nonempty = [value.strip() for value in values if value is not None and value.strip()]
    if not nonempty:
        return ""
    if column.endswith("_chunk_id") or column in {"retrieved_by", "chunk_id"}:
        return ";".join(dict.fromkeys(nonempty))
    if column.endswith("_rank") or column in {"best_rank", "retrieval_method_count"}:
        numbers = []
        for value in nonempty:
            try:
                numbers.append(float(value))
            except ValueError:
                pass
        if numbers:
            selected = min(numbers) if column.endswith("_rank") or column == "best_rank" else max(numbers)
            return str(int(selected)) if selected.is_integer() else str(selected)
    return nonempty[0]


def deduplicate_pool_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("question_number", "").strip(), row.get("pmid", "").strip())].append(row)

    deduplicated: list[dict[str, str]] = []
    for group in grouped.values():
        columns = list(group[0])
        merged = {column: merge_values(column, [row.get(column, "") for row in group]) for column in columns}
        for column in ANNOTATION_FIELDS:
            if column in merged:
                merged[column] = ""
        deduplicated.append(merged)
    return deduplicated


def export_annotation_candidates(
    relevance_pool_path: Path,
    documents_path: Path,
    output_dir: Path,
) -> Path:
    pool_rows = read_csv(relevance_pool_path)
    if not pool_rows:
        raise ValueError("The relevance pool is empty")
    missing_columns = REQUIRED_POOL_COLUMNS - set(pool_rows[0])
    if missing_columns:
        raise ValueError(f"Relevance pool is missing columns: {sorted(missing_columns)}")

    with documents_path.open("rb") as handle:
        documents = pickle.load(handle)
    abstract_lookup, abstract_conflict_count = build_abstract_lookup(documents)
    merged_pool = deduplicate_pool_rows(pool_rows)

    enriched_rows: list[dict[str, str]] = []
    missing_rows: list[dict[str, str]] = []
    for row in merged_pool:
        pmid = row.get("pmid", "").strip()
        abstract = abstract_lookup.get(pmid)
        row = dict(row)
        row["chunk_id"] = ";".join(
            dict.fromkeys(
                value
                for column, value in row.items()
                if column.endswith("_chunk_id") and value.strip()
                for value in value.split(";")
            )
        )
        row["abstract_text"] = abstract["abstract_text"] if abstract else ""
        row["abstract_source"] = abstract["abstract_source"] if abstract else "missing"
        for metadata_column in ("title", "journal", "year"):
            row[metadata_column] = abstract.get(metadata_column, "") if abstract else ""
        row["relevance_label"] = ""
        row["justification"] = ""
        enriched_rows.append(row)
        if not row["abstract_text"]:
            missing_rows.append(
                {
                    "question_number": row.get("question_number", ""),
                    "pmid": pmid,
                    "retrieved_by": row.get("retrieved_by", ""),
                    "chunk_id": row.get("chunk_id", ""),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    original_fields = list(pool_rows[0])
    fields = original_fields + [field for field in OUTPUT_FIELDS + ["abstract_source", "title", "journal", "year"] if field not in original_fields]
    write_csv(output_dir / "retrieval_relevance_pool_v1_with_abstracts.csv", fields, enriched_rows)

    for question_number in sorted({row["question_number"] for row in enriched_rows}):
        question_rows = [row for row in enriched_rows if row["question_number"] == question_number]
        write_csv(output_dir / f"question_{int(question_number):02d}_annotation.csv", fields, question_rows)

    missing_fields = ["question_number", "pmid", "retrieved_by", "chunk_id"]
    write_csv(output_dir / "missing_abstracts.csv", missing_fields, missing_rows)

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "relevance_pool_path": str(relevance_pool_path),
        "documents_path": str(documents_path),
        "input_row_count": len(pool_rows),
        "output_row_count": len(enriched_rows),
        "deduplicated_row_count": len(pool_rows) - len(enriched_rows),
        "missing_abstract_count": len(missing_rows),
        "abstract_conflict_pmid_count": abstract_conflict_count,
        "annotation_fields_forced_blank": ANNOTATION_FIELDS,
        "rows_by_question": {
            question: sum(row["question_number"] == question for row in enriched_rows)
            for question in sorted({row["question_number"] for row in enriched_rows})
        },
    }
    (output_dir / "annotation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relevance-pool", type=Path, required=True)
    parser.add_argument("--documents", type=Path, default=Path("data/corpus_v1/egfr_nsclc_documents.pkl"))
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = export_annotation_candidates(args.relevance_pool, args.documents, args.output_dir)
    print(f"Saved annotation candidates to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
