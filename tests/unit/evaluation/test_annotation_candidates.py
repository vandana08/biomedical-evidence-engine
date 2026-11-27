import csv
import pickle
from types import SimpleNamespace

from scripts.annotation.export_annotation_candidates import export_annotation_candidates


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)


def test_left_join_deduplicates_q1_and_blanks_annotations(tmp_path):
    pool = tmp_path / "pool.csv"
    write_csv(pool, [
        {"question_number": "1", "question": "q", "pmid": "p1", "bm25_rank": "1", "bm25_chunk_id": "c1", "relevance_label": "old", "justification": "old"},
        {"question_number": "1", "question": "q", "pmid": "p1", "bm25_rank": "", "bm25_chunk_id": "c2", "relevance_label": "", "justification": ""},
        {"question_number": "1", "question": "q", "pmid": "missing", "bm25_rank": "2", "bm25_chunk_id": "c3", "relevance_label": "", "justification": ""},
    ])
    documents = [SimpleNamespace(metadata={"pmid": "p1", "abstract_sections": [{"label": "RESULTS", "text": "Full abstract."}]}, page_content="chunk")]
    documents_path = tmp_path / "documents.pkl"
    with documents_path.open("wb") as handle:
        pickle.dump(documents, handle)

    output = export_annotation_candidates(pool, documents_path, tmp_path / "out")
    rows = list(csv.DictReader((output / "question_01_annotation.csv").open(encoding="utf-8")))
    assert len(rows) == 2
    p1 = next(row for row in rows if row["pmid"] == "p1")
    assert p1["chunk_id"] == "c1;c2"
    assert p1["abstract_text"] == "RESULTS: Full abstract."
    assert p1["relevance_label"] == ""
    assert p1["justification"] == ""
    missing = list(csv.DictReader((output / "missing_abstracts.csv").open(encoding="utf-8")))
    assert [row["pmid"] for row in missing] == ["missing"]
