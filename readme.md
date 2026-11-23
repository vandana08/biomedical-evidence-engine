# Biomedical Evidence Engine

A Streamlit-based biomedical question-answering assistant over PubMed abstracts. The application combines semantic FAISS retrieval, BM25 keyword retrieval, reciprocal-rank fusion, and a cross-encoder reranker before generating an answer with OpenAI models.

The included corpus focuses on EGFR-mutant non-small cell lung cancer (NSCLC) treatment evidence.

## Features

- Searches a local corpus of PubMed abstracts.
- Combines vector and lexical retrieval with `HybridRetriever`.
- Reranks results using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- Generates context-grounded answers with `gpt-4o-mini`.
- Displays retrieved abstracts, PMIDs, journals, and request latency in the Streamlit UI.
- Supports corpus rebuilding and RAGAS-based evaluation.

## Requirements

- Python 3.11 recommended
- An OpenAI API key
- Internet access for OpenAI requests, PubMed ingestion, and the first download of the sentence-transformer reranker

## Setup

From the project directory, create and activate a virtual environment:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, activate from Command Prompt instead:

```cmd
venv\Scripts\activate.bat
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your_openai_api_key
```

## Run the application

The repository includes a prebuilt corpus under `data/`. Start the Streamlit app with:

```powershell
streamlit run main.py
```

Open the local URL shown by Streamlit, then enter a biomedical question. For example:

```text
How does osimertinib affect progression-free survival in EGFR-mutant NSCLC?
```

## Rebuild the PubMed corpus

To fetch current PubMed records and recreate the FAISS, BM25, document, and metadata files:

```powershell
python build_corpus.py
```

The generated files are written to `data/`:

- `egfr_nsclc_faiss/` — FAISS index and metadata
- `egfr_nsclc_bm25.pkl` — BM25 index
- `egfr_nsclc_documents.pkl` — serialized LangChain documents
- `corpus_metadata.json` — corpus version and query metadata

The corpus builder currently uses two EGFR/NSCLC PubMed queries and fetches up to 500 records per query. Rebuilding requires PubMed and OpenAI access and may take time.

## Evaluation

Generate an evaluation dataset from the local corpus:

```powershell
python src\generate_eval_dataset.py
```

Run the RAGAS evaluation:

```powershell
python src\evaluate_rag.py
```

The evaluation uses the questions in `data/eval_dataset.csv` and reports faithfulness, answer relevancy, context precision, and context recall.

## Project structure

```text
.
├── main.py                 # Streamlit application
├── build_corpus.py         # PubMed ingestion and index construction
├── requirements.txt        # Python dependencies
├── data/                   # Corpus indexes, documents, and evaluation data
├── prompt/                 # Answer-generation prompt
└── src/
    ├── pubmed_ingestor.py  # PubMed retrieval and document parsing
    ├── load_corpus.py      # Load persisted indexes and documents
    ├── hybrid_retriever.py # FAISS + BM25 retrieval and fusion
    ├── reranker.py         # Cross-encoder reranking
    ├── pipeline.py         # Retrieval and answer-generation pipeline
    └── evaluate_rag.py     # RAGAS evaluation
```

## Notes

- Answers are constrained to the retrieved PubMed context and are not a substitute for clinical advice.
- The FAISS loader enables LangChain dangerous deserialization because the persisted index is a project-generated local artifact. Only load trusted index files.
- Keep `.env` out of version control and never commit API keys.
