# Biomedical Evidence Engine

A Streamlit-based biomedical question-answering assistant over PubMed abstracts. It combines FAISS semantic retrieval, BM25 keyword retrieval, reciprocal-rank fusion, and cross-encoder reranking before generating a context-grounded answer with OpenAI models.

The current corpus focuses on EGFR-mutant non-small cell lung cancer (NSCLC) treatment evidence. Corpus generation and validation artifacts are versioned separately under `data/corpus_v1/`.

## Features

- Searches a local PubMed abstract corpus.
- Combines vector and lexical retrieval through `HybridRetriever`.
- Reranks results with `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- Generates answers with `gpt-4o-mini` using only retrieved context.
- Displays retrieved abstracts, PMIDs, journals, and retrieval/generation latency.
- Preserves chunk-level provenance with deterministic `chunk_id` values and matched-query metadata.
- Includes corpus validation, source audits, evidence-schema documentation, annotation guidance, and baseline evaluation artifacts.

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

From Command Prompt, use:

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
NCBI_EMAIL=your_email@example.com
```

`OPENAI_API_KEY` is required when running the application or building the corpus. `NCBI_EMAIL` identifies the requester for PubMed/NCBI API requests and is required when rebuilding the corpus. The existing prebuilt corpus can be used without rebuilding, but an OpenAI API key is still required for embeddings and answer generation.

## Run the application

The repository includes a prebuilt corpus under `data/`. Start the Streamlit app with:

```powershell
streamlit run main.py
```

Open the local URL shown by Streamlit and enter a biomedical question, for example:

```text
How does osimertinib affect progression-free survival in EGFR-mutant NSCLC?
```

## Build the versioned PubMed corpus

To fetch current PubMed records and rebuild the versioned corpus:

```powershell
python build_corpus.py
```

The builder currently runs two EGFR/NSCLC queries, fetches up to 500 records per query, parses abstracts into overlapping chunks, and removes duplicate chunks using:

```text
PMID + start_index + exact chunk text
```

Both retrieval indexes are created from the same ordered, deduplicated chunk list. Outputs are written to `data/corpus_v1/`:

- `egfr_nsclc_faiss/` — FAISS index
- `egfr_nsclc_bm25.pkl` — BM25 index
- `egfr_nsclc_documents.pkl` — serialized LangChain documents
- `corpus_metadata.json` — corpus version, counts, queries, and build settings
- `corpus_parse_errors.json` — records skipped during parsing

The current checked-in metadata records 957 unique PMIDs, 2,638 unique chunks, 58 duplicate chunk occurrences removed, and zero parse errors. Rebuilding requires PubMed and OpenAI access.

## Validate the corpus

After building or restoring the corpus, run:

```powershell
python validate_corpus.py
```

Validation loads the metadata, serialized documents, BM25 index, and FAISS index, then reports count consistency, PMID coverage, chunk-ID presence and uniqueness, and sample abstract-section metadata.

## Evaluation

Generate an evaluation dataset from the local corpus:

```powershell
python src\generate_eval_dataset.py
```

Run the RAGAS evaluation:

```powershell
python src\evaluate_rag.py
```

The evaluation uses `data/eval_dataset.csv` and reports faithfulness, answer relevancy, context precision, and context recall.

## Evidence and audit documentation

The `docs/` directory contains the supporting evidence-quality artifacts:

- `evidence_schema_v0.1.md` — evidence-record fields and controlled vocabularies
- `manual_annotation_guideline_v0.1_full_abstract.md` — annotation rules and quality checklist
- `source_verification_audit.md` — source-level verification and corrections
- `gold_standard_consistency_review_v1.md` — gold-standard structural and consistency review
- `baseline_evaluation.md` — baseline questions, observations, latency, and limitations
- `audit/` — corpus completeness, authorship, publication-year, topic, and prior-corpus audit reports

## Project structure

```text
.
├── main.py                    # Streamlit application
├── build_corpus.py            # PubMed ingestion and corpus_v1 construction
├── validate_corpus.py         # Index, metadata, and provenance checks
├── requirements.txt           # Python dependencies
├── data/
│   ├── corpus_v1/             # Current versioned corpus artifacts
│   ├── corpus_metadata.json   # Earlier/root-level corpus artifact, if present
│   ├── eval_dataset.csv       # Evaluation questions and references
│   └── gold_standard/         # Pilot evidence annotations
├── docs/                      # Evidence schema, audits, guidelines, and reports
├── prompt/                    # Answer-generation prompt
└── src/
    ├── pubmed_ingestor.py     # PubMed retrieval and parsing
    ├── load_corpus.py         # Load persisted retrieval artifacts
    ├── hybrid_retriever.py    # FAISS + BM25 fusion
    ├── reranker.py            # Cross-encoder reranking
    ├── pipeline.py            # Retrieval and answer-generation pipeline
    ├── generate_eval_dataset.py
    └── evaluate_rag.py        # RAGAS evaluation
```

## Notes

- Answers are evidence-grounded summaries, not medical advice or a substitute for clinical review.
- Corpus rebuilding can change the retrieved evidence as PubMed records and parsing results change.
- The FAISS loader enables LangChain dangerous deserialization for trusted local project artifacts only.
- Keep `.env` out of version control and never commit API keys.
