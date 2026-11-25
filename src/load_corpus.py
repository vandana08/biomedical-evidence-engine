import streamlit as st
from langchain_community.vectorstores import FAISS
import pickle
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()


def load_corpus():

    faiss_db = FAISS.load_local(
        "data/corpus_v1/egfr_nsclc_faiss",
        OpenAIEmbeddings(model="text-embedding-3-small"),
        allow_dangerous_deserialization=True
    )

    with open("data/corpus_v1/egfr_nsclc_bm25.pkl", "rb") as f:
        bm25 = pickle.load(f)

    with open("data/corpus_v1/egfr_nsclc_documents.pkl", "rb") as f:
        documents = pickle.load(f)

    return faiss_db, bm25, documents
