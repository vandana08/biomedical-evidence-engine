"""Run the five Day 1 baseline questions against data/corpus_v1.

Run from the repository root:
    python run_baseline_comparison.py

Requires a rebuilt corpus and OPENAI_API_KEY in .env.
Writes question_results.csv, retrieved_chunks.jsonl and run_metadata.json
under outputs/baseline_comparison_<timestamp>/.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from biomedical_evidence_engine.config.questions import BASELINE_QUESTIONS
from biomedical_evidence_engine.corpus.loader import load_corpus
from biomedical_evidence_engine.app.pipeline import run_rag

def json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return list(value)
    return str(value)

def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY not found. Add it to .env.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path("outputs") / f"baseline_comparison_{stamp}"
    out.mkdir(parents=True, exist_ok=True)

    print("Loading corpus...")
    faiss_db, bm25, documents = load_corpus()
    print(f"Loaded {len(documents)} chunks.")

    result_rows, chunk_rows = [], []
    for n, question in enumerate(BASELINE_QUESTIONS, start=1):
        print(f"\n[{n}/5] {question}")
        answer, docs, latency = run_rag(
            query=question,
            faiss_db=faiss_db,
            bm25_index=bm25,
            documents=documents,
            return_latency=True,
        )

        pmids = []
        for rank, doc in enumerate(docs, start=1):
            md = {k: json_safe(v) for k, v in doc.metadata.items()}
            pmid = str(md.get("pmid", "")).strip()
            if pmid and pmid not in pmids:
                pmids.append(pmid)
            chunk_rows.append({
                "question_number": n,
                "question": question,
                "rank": rank,
                "pmid": pmid,
                "chunk_id": md.get("chunk_id"),
                "title": md.get("title"),
                "metadata": md,
                "chunk_text": doc.page_content,
            })

        result_rows.append({
            "question_number": n,
            "question": question,
            "answer": answer,
            "retrieved_chunk_count": len(docs),
            "retrieved_pmids": ";".join(pmids),
            "retrieval_ms": round(latency["retrieval_ms"], 2),
            "generation_ms": round(latency["generation_ms"], 2),
            "total_ms": round(latency["total_ms"], 2),
        })
        print(f"Retrieved {len(docs)} chunks; {len(pmids)} unique PMIDs: {', '.join(pmids)}")
        print(f"Latency: {latency['total_ms']:.0f} ms "
              f"(retrieval {latency['retrieval_ms']:.0f} ms; "
              f"generation {latency['generation_ms']:.0f} ms)")
        print("Answer:", answer)

    pd.DataFrame(result_rows).to_csv(out / "question_results.csv", index=False)
    with (out / "retrieved_chunks.jsonl").open("w", encoding="utf-8") as f:
        for row in chunk_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    metadata = {
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_path": "data/corpus_v1",
        "question_count": len(BASELINE_QUESTIONS),
        "pipeline": "biomedical_evidence_engine.app.pipeline.run_rag",
        "note": (
            "run_rag forwards its top_k parameter to HybridRetriever. "
            "Retrieved corpus chunks are identified by stable chunk_id metadata."
        ),
    }
    (out / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"\nSaved results to: {out.resolve()}")

if __name__ == "__main__":
    main()
