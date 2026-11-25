
import os
import json
import pickle

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
load_dotenv()

DATA_DIR = os.path.join("data", "corpus_v1")

# 1. Load metadata
with open(os.path.join(DATA_DIR, "corpus_metadata.json")) as f:
    metadata = json.load(f)

# 2. Load saved documents
with open(os.path.join(DATA_DIR, "egfr_nsclc_documents.pkl"), "rb") as f:
    documents = pickle.load(f)

# 3. Load BM25
with open(os.path.join(DATA_DIR, "egfr_nsclc_bm25.pkl"), "rb") as f:
    bm25 = pickle.load(f)

# 4. Load FAISS
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

faiss_db = FAISS.load_local(
    os.path.join(DATA_DIR, "egfr_nsclc_faiss"),
    embeddings,
    allow_dangerous_deserialization=True
)

# 5. Validate counts
print("\n--- Corpus Validation ---")
print("Metadata chunks:", metadata["num_chunks"])
print("Saved documents:", len(documents))
print("BM25 documents:", len(bm25.doc_freqs))
print("FAISS vectors:", faiss_db.index.ntotal)

print("\n--- Metadata checks ---")
print("All chunks have PMID:",
      all(d.metadata.get("pmid") for d in documents))

print("All chunks have chunk_id:",
      all(d.metadata.get("chunk_id") for d in documents))

print("Unique chunk IDs:",
      len({d.metadata.get("chunk_id") for d in documents}))

print("Unique PMIDs:",
      len({d.metadata.get("pmid") for d in documents}))

print("\n--- Abstract section sample ---")
for doc in documents[:3]:
    print("\nPMID:", doc.metadata.get("pmid"))
    print(doc.page_content[:500])
    print("Section metadata:",
          doc.metadata.get("abstract_sections"))

assert len(documents) == metadata["num_chunks"]
assert len({d.metadata["chunk_id"] for d in documents}) == len(documents)
assert all(d.page_content.strip() for d in documents)
assert all(d.metadata.get("pmid") for d in documents)
assert len(bm25.doc_freqs) == len(documents)
assert faiss_db.index.ntotal == len(documents)
