"""Load persisted corpus retrieval artifacts."""

import pickle
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

load_dotenv()


def load_corpus(data_dir: str | Path = "data/corpus_v1"):
    data_dir = Path(data_dir)
    faiss_db = FAISS.load_local(
        str(data_dir / "egfr_nsclc_faiss"),
        OpenAIEmbeddings(model="text-embedding-3-small"),
        allow_dangerous_deserialization=True,
    )
    with (data_dir / "egfr_nsclc_bm25.pkl").open("rb") as handle:
        bm25 = pickle.load(handle)
    with (data_dir / "egfr_nsclc_documents.pkl").open("rb") as handle:
        documents = pickle.load(handle)
    return faiss_db, bm25, documents
