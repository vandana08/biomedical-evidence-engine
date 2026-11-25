from Bio import Entrez
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
load_dotenv()



Entrez.email = os.getenv("NCBI_EMAIL")
if not Entrez.email:
    raise ValueError("Please configure NCBI_EMAIL in your .env file.")

class PubMedIngestor():
    def __init__(self, query, max_records=50):
        self.query = query
        self.max_records = max_records
        self.documents = []
        self.chunks = []
        self.parse_errors = []

    def get_pubmed_ids(self):
        print("Getting PubMed Ids...")
        if not self.query or len(self.query.strip()) < 3:
            raise ValueError("Query too short or empty.")
        
        with Entrez.esearch(
            db="pubmed",
            term=self.query,
            retmax=self.max_records,
        ) as handle:
            record = Entrez.read(handle)

        self.pubmed_ids = record.get("IdList", [])
        if not self.pubmed_ids:
            raise RuntimeError("No PubMed articles found for the given query.")


    def fetch_pubmed_records(self):
        print("Fetching PubMed records...")
        if not getattr(self, "pubmed_ids", None):
            raise RuntimeError("Cannot fetch records: no PubMed IDs available.")

        with Entrez.efetch(
            db="pubmed",
            id=self.pubmed_ids,
            rettype="xml",
            retmode="text",
        ) as handle:
            self.records = Entrez.read(handle)

    @staticmethod
    def _extract_abstract(article_info):
        """Return complete abstract text and its structured section metadata."""
        abstract_data = article_info.get("Abstract")
        if not abstract_data:
            return "", []

        abstract_parts = abstract_data.get("AbstractText", [])
        if isinstance(abstract_parts, (str, bytes)):
            abstract_parts = [abstract_parts]

        rendered_sections = []
        section_metadata = []

        for part in abstract_parts:
            section_text = str(part).strip()
            if not section_text:
                continue

            attributes = getattr(part, "attributes", {}) or {}
            label = attributes.get("Label")
            nlm_category = attributes.get("NlmCategory")
            section_label = label or nlm_category

            if section_label:
                rendered_sections.append(f"{section_label}: {section_text}")
            else:
                rendered_sections.append(section_text)

            section_metadata.append({
                "label": str(label) if label else None,
                "nlm_category": str(nlm_category) if nlm_category else None,
                "text": section_text,
            })

        return "\n".join(rendered_sections), section_metadata

    @staticmethod
    def _extract_authors(author_list):
        names = []
        for author in author_list or []:
            if author.get("LastName"):
                last_name = str(author["LastName"])
                initials = author.get("Initials")
                names.append(f"{last_name} {initials}".strip() if initials else last_name)
            elif author.get("CollectiveName"):
                names.append(str(author["CollectiveName"]))
        return ", ".join(names)

    def parse_pubmed_to_document(self):
        print("Parsing PubMed records to documents...")
        self.documents = []
        self.parse_errors = []

        for article in self.records.get("PubmedArticle", []):
            try:
                medline = article["MedlineCitation"]
                article_info = medline["Article"]

                pmid = str(medline["PMID"])
                title = str(article_info.get("ArticleTitle", ""))
                abstract, abstract_sections = self._extract_abstract(article_info)

                if not abstract:
                    continue

                journal_info = article_info.get("Journal", {})
                journal = str(journal_info.get("Title", "Unknown"))
                pub_date = (
                    journal_info.get("JournalIssue", {}).get("PubDate", {})
                )
                year = str(pub_date.get("Year", "Unknown"))

                authors = self._extract_authors(
                    article_info.get("AuthorList", [])
                )

                mesh_terms = []
                for heading in medline.get("MeshHeadingList", []):
                    descriptor = heading.get("DescriptorName")
                    if descriptor:
                        mesh_terms.append(str(descriptor))

                self.documents.append(
                    Document(
                        page_content=abstract,
                        metadata={
                            "pmid": pmid,
                            "title": title,
                            "journal": journal,
                            "year": year,
                            "authors": authors,
                            "keywords": mesh_terms,
                            "abstract_sections": abstract_sections,
                            "source": "PubMed",
                        },
                    )
                )

            except Exception as exc:
                self.parse_errors.append({
                    "pmid": str(
                        article.get("MedlineCitation", {}).get("PMID", "Unknown")
                    ),
                    "error": str(exc),
                })
                print(f"Skipping one article due to parsing error: {exc}")

    def split_documents(self):
        print("Splitting documents...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True,
        )
        self.chunks = splitter.split_documents(self.documents)

    def embed_documents(self, docs=None):
        docs = docs if docs is not None else self.chunks
        if not docs:
            raise ValueError("No documents supplied for embedding.")
        print("Embedding documents...")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        return FAISS.from_documents(docs, embeddings)

    def bm25_index(self, docs=None):
        docs = docs if docs is not None else self.chunks
        if not docs:
            raise ValueError("No documents supplied for BM25 indexing.")
        print("Creating BM25 index...")
        tokenized_corpus = [doc.page_content.lower().split() for doc in docs]
        return BM25Okapi(tokenized_corpus)

    def invoke(self):
        self.get_pubmed_ids()
        self.fetch_pubmed_records()
        self.parse_pubmed_to_document()
        self.split_documents()
        return {
            "documents": self.chunks,
            "source_documents": self.documents,
            "parse_errors": self.parse_errors,
        }



        
