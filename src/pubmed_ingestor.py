from Bio import Entrez
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import ssl
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
# Bypass SSL verification
ssl._create_default_https_context = ssl._create_unverified_context
load_dotenv()



Entrez.email = "kvandana1992@gmail.com"

class PubMedIngestor():
    def __init__(self, query, max_records=50):
        self.query = query
        self.max_records = max_records

    def get_pubmed_ids(self):
        print("Getting PubMed Ids...")
        if not self.query or len(self.query.strip()) < 3:
            raise ValueError("Query too short or empty.")
        handle = Entrez.esearch(db="pubmed", term=self.query,
                                retmax=self.max_records)
        record = Entrez.read(handle)
        handle.close()
        if not record.get("IdList"):
            raise RuntimeError("No PubMed articles found for the given query.")
        self.pubmed_ids = record["IdList"]


    def fetch_pubmed_records(self):
        print("Fetching PubMed Records...")
        if not hasattr(self, 'pubmed_ids') or not self.pubmed_ids:
            raise RuntimeError("Cannot fetch records: No PubMed IDs available.")
        handle = Entrez.efetch(db="pubmed", id=self.pubmed_ids, rettype="xml", retmode="text")
        self.records = Entrez.read(handle)
        handle.close()

    def parse_pubmed_to_document(self):
        print("Parsing Pubmed records to documents...")
        abstracts_with_metadata = []
        for article in self.records["PubmedArticle"]:
            try:
                medline = article["MedlineCitation"]
                article_info = medline["Article"]

                pmid = str(medline["PMID"])
                title = article_info["ArticleTitle"]
                abstract = article_info["Abstract"]["AbstractText"][0] if 'Abstract' in article_info else ""
                journal = article_info["Journal"]["Title"]
                year = article_info["Journal"]["JournalIssue"]["PubDate"].get("Year", "Unknown")
                authors = ", ".join([
                    f"{a['LastName']} {a['Initials']}"
                    for a in article_info.get("AuthorList", []) if "LastName" in a
                ])
                mesh_terms = []
                if "MeshHeadingList" in medline:
                    mesh_terms = [str(heading["DescriptorName"]) for heading in medline["MeshHeadingList"]]


                if abstract:  # Ensure we only collect entries with abstract
                    abstracts_with_metadata.append({
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract,
                        "journal": journal,
                        "year": year,
                        "authors": authors,
                        "mesh_terms": mesh_terms
                    })
            except Exception as e:
                print(f"Skipping one article due to error: {e}")
        
        self.documents = [
            Document(
                page_content=entry["abstract"],
                metadata={
                    "pmid": entry["pmid"],
                    "title": entry["title"],
                    "journal": entry["journal"],
                    "year": entry["year"],
                    "authors": entry["authors"],
                    "keywords": entry.get("mesh_terms", []),
                    "source": "PubMed"
                }
            )
            for entry in abstracts_with_metadata
        ]
    
    def split_documents(self):
        print("Splitting Documents...")
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.chunks = splitter.split_documents(self.documents)

    def embed_documents(self, docs=None):
        print("Embedding documents...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = FAISS.from_documents(docs, embeddings)
        return vector_store
    
    def bm25_index(self, docs=None):
        print("Creating BM25 index...")
        tokenized_corpus = [doc.page_content.lower().split(" ") for doc in docs]
        bm25 = BM25Okapi(tokenized_corpus)
        return bm25
    
    def invoke(self):
        self.get_pubmed_ids()
        self.fetch_pubmed_records()
        self.parse_pubmed_to_document()
        self.split_documents()
        #vector_store_db = self.embed_documents()
        #bm25_index = self.bm25_index()
        # return {"faiss": vector_store_db, "bm25_index": bm25_index, "documents": self.chunks}
        return {"documents": self.chunks}
    



        
