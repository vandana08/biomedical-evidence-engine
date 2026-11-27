"""Validate persisted corpus artifacts."""

import json
import os
import pickle


def main():
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings

    data_dir = os.path.join("data", "corpus_v1")
    with open(os.path.join(data_dir, "corpus_metadata.json")) as handle:
        metadata = json.load(handle)
    with open(os.path.join(data_dir, "egfr_nsclc_documents.pkl"), "rb") as handle:
        documents = pickle.load(handle)
    with open(os.path.join(data_dir, "egfr_nsclc_bm25.pkl"), "rb") as handle:
        bm25 = pickle.load(handle)
    faiss_db = FAISS.load_local(
        os.path.join(data_dir, "egfr_nsclc_faiss"),
        OpenAIEmbeddings(model="text-embedding-3-small"),
        allow_dangerous_deserialization=True,
    )

    print("\n--- Corpus Validation ---")
    print("Metadata chunks:", metadata["num_chunks"])
    print("Saved documents:", len(documents))
    print("BM25 documents:", len(bm25.doc_freqs))
    print("FAISS vectors:", faiss_db.index.ntotal)
    print("\n--- Metadata checks ---")
    print("All chunks have PMID:", all(d.metadata.get("pmid") for d in documents))
    print("All chunks have chunk_id:", all(d.metadata.get("chunk_id") for d in documents))
    print("Unique chunk IDs:", len({d.metadata.get("chunk_id") for d in documents}))
    print("Unique PMIDs:", len({d.metadata.get("pmid") for d in documents}))
    for doc in documents[:3]:
        print("\nPMID:", doc.metadata.get("pmid"))
        print(doc.page_content[:500])
        print("Section metadata:", doc.metadata.get("abstract_sections"))

    assert len(documents) == metadata["num_chunks"]
    assert len({d.metadata["chunk_id"] for d in documents}) == len(documents)
    assert all(d.page_content.strip() for d in documents)
    assert all(d.metadata.get("pmid") for d in documents)
    assert len(bm25.doc_freqs) == len(documents)
    assert faiss_db.index.ntotal == len(documents)


if __name__ == "__main__":
    main()
