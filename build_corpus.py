import hashlib
import json
import os
import pickle
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from rank_bm25 import BM25Okapi

from src.pubmed_ingestor import PubMedIngestor

load_dotenv()

# Keep the rebuilt corpus separate from existing baseline artifacts.
DATA_DIR = os.path.join("data", "corpus_v1")
os.makedirs(DATA_DIR, exist_ok=True)

QUERIES = [
    """
    (
      "non-small cell lung cancer"
      AND (EGFR OR "EGFR mutation" OR L858R OR T790M)
      AND (osimertinib OR gefitinib OR erlotinib OR afatinib)
    )
    """,
    """
    (
      "lung adenocarcinoma"
      AND (EGFR OR L858R OR T790M)
      AND ("drug resistance" OR "treatment outcome" OR "progression-free survival")
    )
    """
]


def _chunk_key(doc):
    """Identify the same chunk returned by overlapping PubMed queries."""
    pmid = str(doc.metadata.get("pmid", ""))
    start_index = doc.metadata.get("start_index")
    content = doc.page_content.strip()

    # start_index distinguishes repeated identical text at different
    # positions within one abstract, when available.
    if start_index is not None:
        return pmid, int(start_index), content
    return pmid, content


def deduplicate_chunks(chunks, query_by_chunk):
    unique = {}

    for doc in chunks:
        key = _chunk_key(doc)
        if key not in unique:
            metadata = dict(doc.metadata)
            metadata["matched_queries"] = [query_by_chunk[id(doc)]]
            unique[key] = doc.__class__(
                page_content=doc.page_content,
                metadata=metadata,
            )
        else:
            existing = unique[key]
            matched = existing.metadata.setdefault("matched_queries", [])
            query = query_by_chunk[id(doc)]
            if query not in matched:
                matched.append(query)

    return list(unique.values())


def build_corpus(max_records=500):
    all_chunks = []
    query_by_chunk = {}
    parse_errors = []
    source_pmid_sets = {}

    for query_index, query in enumerate(QUERIES, start=1):
        print(f"Fetching query {query_index}/{len(QUERIES)}...")
        ingestor = PubMedIngestor(query, max_records=max_records)
        result = ingestor.invoke()

        chunks = result["documents"]
        all_chunks.extend(chunks)
        for chunk in chunks:
            query_by_chunk[id(chunk)] = query

        parse_errors.extend(result.get("parse_errors", []))
        source_pmid_sets[query_index] = {
            str(doc.metadata["pmid"])
            for doc in result.get("source_documents", [])
            if doc.metadata.get("pmid") is not None
        }

    unique_chunks = deduplicate_chunks(all_chunks, query_by_chunk)

    if not unique_chunks:
        raise RuntimeError("Corpus build stopped: no abstract chunks were produced.")

    unique_pmids = {
        str(doc.metadata["pmid"])
        for doc in unique_chunks
        if doc.metadata.get("pmid") is not None
    }

    # Stable IDs make chunk-level provenance and later evaluation easier.
    for doc in unique_chunks:
        start = doc.metadata.get("start_index", "NA")
        raw_id = f"{doc.metadata.get('pmid', '')}|{start}|{doc.page_content}"
        doc.metadata["chunk_id"] = hashlib.sha256(
            raw_id.encode("utf-8")
        ).hexdigest()[:16]

    print(f"Unique PMIDs: {len(unique_pmids)}")
    print(f"Unique chunks: {len(unique_chunks)}")
    print(f"Duplicate chunk occurrences removed: {len(all_chunks) - len(unique_chunks)}")
    print(f"Parsing errors: {len(parse_errors)}")

    # Build both retrieval indexes from exactly the same ordered chunk list.
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    faiss_db = FAISS.from_documents(unique_chunks, embeddings)
    faiss_db.save_local(os.path.join(DATA_DIR, "egfr_nsclc_faiss"))

    tokenized_corpus = [doc.page_content.lower().split() for doc in unique_chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(os.path.join(DATA_DIR, "egfr_nsclc_bm25.pkl"), "wb") as file:
        pickle.dump(bm25, file)

    with open(os.path.join(DATA_DIR, "egfr_nsclc_documents.pkl"), "wb") as file:
        pickle.dump(unique_chunks, file)

    corpus_meta = {
        "corpus_name": "EGFR-NSCLC",
        "version": "v1.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "num_unique_pmids": len(unique_pmids),
        "num_chunks": len(unique_chunks),
        "num_chunk_occurrences_before_deduplication": len(all_chunks),
        "num_duplicate_chunk_occurrences_removed": len(all_chunks) - len(unique_chunks),
        "num_parse_errors": len(parse_errors),
        "queries_used": QUERIES,
        "query_result_unique_pmids": {
            str(index): len(pmids)
            for index, pmids in source_pmid_sets.items()
        },
        "focus": "EGFR-mutant NSCLC treatment evidence",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "embedding_model": "text-embedding-3-small",
        "deduplication_key": "PMID + start_index + exact chunk text",
    }

    with open(os.path.join(DATA_DIR, "corpus_metadata.json"), "w", encoding="utf-8") as file:
        json.dump(corpus_meta, file, indent=4)

    with open(os.path.join(DATA_DIR, "corpus_parse_errors.json"), "w", encoding="utf-8") as file:
        json.dump(parse_errors, file, indent=4)

    print(f"Corpus built successfully in: {DATA_DIR}")


if __name__ == "__main__":
    build_corpus()
