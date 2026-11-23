import os
import json
import pickle
import faiss
from datetime import datetime
from rank_bm25 import BM25Okapi
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from src.pubmed_ingestor import PubMedIngestor
from dotenv import load_dotenv
load_dotenv()


DATA_DIR = "data"
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

def build_corpus(max_records=500):

    all_docs = []

    for query in QUERIES:
        print(f"Fetching for query: {query}")
        ingestor = PubMedIngestor(query, max_records=max_records)
        store = ingestor.invoke()
        all_docs.extend(store["documents"])

    # Deduplicate by PMID
    unique_docs = list({
        doc.metadata["pmid"]: doc for doc in all_docs
    }.values())

    print(f"Total unique documents: {len(unique_docs)}")

    # -------- Build FAISS --------
    faiss_db = ingestor.embed_documents(docs=unique_docs)
    faiss_db.save_local(os.path.join(DATA_DIR, "egfr_nsclc_faiss"))

    # -------- Build BM25 --------
    bm25 = ingestor.bm25_index(docs=unique_docs)
    with open(os.path.join(DATA_DIR, "egfr_nsclc_bm25.pkl"), "wb") as f:
        pickle.dump(bm25, f)

    # -------- Save Documents --------
    with open(os.path.join(DATA_DIR, "egfr_nsclc_documents.pkl"), "wb") as f:
        pickle.dump(unique_docs, f)

    # -------- Corpus Metadata --------
    corpus_meta = {
        "corpus_name": "EGFR-NSCLC",
        "version": "v1.0",
        "created_on": datetime.now().strftime("%Y-%m"),
        "num_documents": len(unique_docs),
        "queries_used": QUERIES,
        "focus": "EGFR-mutant NSCLC treatment evidence"
    }

    with open(os.path.join(DATA_DIR, "corpus_metadata.json"), "w") as f:
        json.dump(corpus_meta, f, indent=4)

    print("Corpus built successfully.")

if __name__ == "__main__":
    build_corpus()
