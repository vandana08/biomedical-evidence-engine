# Biomedical Evidence Engine

A Streamlit-based biomedical question-answering assistant over PubMed abstracts. It combines FAISS semantic retrieval, BM25 keyword retrieval, reciprocal-rank fusion, and cross-encoder reranking before generating a context-grounded answer with OpenAI models.

The current corpus focuses on EGFR-mutant non-small cell lung cancer (NSCLC) treatment evidence. Corpus generation and validation artifacts are versioned separately under `data/corpus_v1/`.

## Features

- Searches a local PubMed abstract corpus.
- Combines vector and lexical retrieval through `HybridRetriever`.
- Provides independent `BM25Retriever`, `DenseRetriever`, and non-reranking
  `HybridRRF` implementations for retrieval comparisons.
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
# For development and tests, use: pip install -r requirements/dev.txt
```

Create a `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your_openai_api_key
NCBI_EMAIL=your_email@example.com
```

`OPENAI_API_KEY` is required when running the application or building the corpus. `NCBI_EMAIL` identifies the requester for PubMed/NCBI API requests and is required when rebuilding the corpus. The existing prebuilt corpus can be used without rebuilding, but an OpenAI API key is still required for embeddings and answer generation.

## Run the application

For a fresh clone, build the local corpus before launching the application:

```powershell
python scripts\corpus\build_corpus.py
```

Corpus building requires access to PubMed/NCBI and available OpenAI API credits for generating embeddings. Once the corpus has been built under `data/corpus_v1/`, start the Streamlit app with:

```powershell
streamlit run main.py
```

## Run the retrieval benchmark

Run the four retrieval experiments (BM25, dense, non-reranking RRF, and the
existing reranking hybrid) against the five baseline questions:

```powershell
python scripts\benchmarks\run_retrieval_benchmark.py
```

Results are written separately under
`outputs/retrieval_benchmark_<timestamp>/`, with per-method
`retrieved_chunks.csv`, `question_summary.csv`, and `run_metadata.json` files.
Use `--top-k 10` to change the result count, or `--output-dir <path>` to choose
an explicit output directory.

To create annotation-ready candidates from a relevance pool, run:

```powershell
python scripts\annotation\export_annotation_candidates.py `
  --relevance-pool outputs/retrieval_benchmark_<timestamp>/retrieval_relevance_pool_v1.csv `
  --output-dir outputs/retrieval_benchmark_<timestamp>/annotation
```

The exporter left-joins the relevance pool to corpus abstracts by PMID,
deduplicates Q1 to one row per paper, reports missing abstracts, and leaves
`relevance_label` and `justification` blank for manual review.

Open the local URL shown by Streamlit and enter a biomedical question, for example:

```text
How does osimertinib affect progression-free survival in EGFR-mutant NSCLC?
```

## Build the versioned PubMed corpus

To fetch current PubMed records and rebuild the versioned corpus:

```powershell
python scripts\corpus\build_corpus.py
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

The current checked-in metadata records 957 unique PMIDs, 2,638 unique chunks, 58 duplicate chunk occurrences removed, and zero parse errors. Rebuilding requires PubMed/NCBI access, a configured `NCBI_EMAIL`, and available OpenAI API credits for embeddings.

## Validate the corpus

After building or restoring the corpus, run:

```powershell
python scripts\corpus\validate_corpus.py
```

Validation loads the metadata, serialized documents, BM25 index, and FAISS index, then reports count consistency, PMID coverage, chunk-ID presence and uniqueness, and sample abstract-section metadata.

## Evaluation

### Retrieval Benchmark — Initial Findings

Four retrieval strategies were evaluated across five biomedical questions:
BM25, dense retrieval, hybrid Reciprocal Rank Fusion (RRF), and hybrid
retrieval with a CrossEncoder reranker.

Dense retrieval achieved the strongest overall ranking performance, with
Precision@5 of 1.00, pooled Recall@5 of 0.2889, MRR of 1.00, and nDCG@5 of
0.7912.

Hybrid retrieval with a CrossEncoder reranker achieved the same binary
relevance metrics as dense retrieval but a slightly lower nDCG@5 of 0.7742. Its
mean latency was approximately 2.5 seconds, compared with 0.86 seconds for
dense retrieval.

BM25 provided the fastest retrieval baseline, with a mean latency of
approximately 21 ms, while hybrid RRF offered an intermediate latency of
approximately 364 ms.

The initial results suggest that dense retrieval provides the best balance of
ranking quality and latency among the evaluated methods. However, the
benchmark is limited to five questions, and pooled recall is calculated
against the judged candidate pool rather than the complete corpus. Further
evaluation with a larger set of questions and independently reviewed
relevance judgments is required before making a definitive retrieval strategy
selection.

The detailed PMID-level evaluation outputs are generated with:

```powershell
python scripts\benchmarks\evaluate_relevance_judgments.py `
  --annotation-dir outputs/retrieval_benchmark_<timestamp>/annotation `
  --benchmark-dir outputs/retrieval_benchmark_<timestamp> `
  --output-dir outputs/retrieval_benchmark_<timestamp>/evaluation
```

Run the repeated latency and retrieval-stability benchmark with a warm-up
query before timing:

```powershell
python scripts\benchmarks\run_retrieval_stability_benchmark.py `
  --output-dir outputs/retrieval_benchmark_<timestamp>/stability
```

The benchmark reports query-time latency, pairwise Jaccard@10, top-five set
and ordering consistency, and rank-sensitive RBO@10. Setup and warm-up time
are excluded from latency measurements.

### Retrieval Repeatability and Latency

**Benchmark provenance:** `retrieval_benchmark_20261126_111147`, using the
`EGFR-NSCLC v1.0` corpus with 957 unique PMIDs and 2,637 chunks.

Each retrieval method was evaluated using five benchmark questions, with three
repeated runs per question. Corpus loading, model initialization, retriever
initialization, and the untimed warm-up query were excluded from latency
measurements.

All four retrieval methods demonstrated identical top-10 result sets and
ranking orders across the three repeated runs for every question. Consequently,
mean Jaccard@10, RBO@10, and Jaccard@5 were all 1.0.

These results indicate complete retrieval-set and ranking-order stability under
the tested configuration. However, three repeated runs are insufficient to
characterize long-term production latency variance or tail latency.

Jaccard measures retrieval-set stability, while RBO measures rank-sensitive
stability. Neither metric evaluates relevance or retrieval quality; these are
assessed separately using relevance-based metrics.

Latency results represent query-time performance after initialization and
should not be interpreted as end-to-end application latency or production
performance.

The exact stability output is available in
[stability_report.md](outputs/retrieval_benchmark_20261126_111147/evaluation_stability/stability_report.md).

| Retriever | Mean latency (ms) | Std. dev. (ms) | Minimum (ms) | Maximum (ms) |
|---|---:|---:|---:|---:|
| BM25 | 4.54 | 1.76 | 2.73 | 8.99 |
| Dense | 386.07 | 56.62 | 304.02 | 510.92 |
| Hybrid RRF | 403.62 | 49.66 | 294.83 | 510.21 |
| Hybrid + CrossEncoder | 1,794.18 | 173.03 | 1,473.08 | 2,057.63 |

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
- `retrieval_benchmark_evaluation.md` — current PMID-level retrieval results and limitations
- `retrieval_metrics_guide.md` — formulas, examples, and interpretation of retrieval metrics
- `retrieval_stability_evaluation.md` — latency and repeated-run stability methodology
- `architecture.md` — package, script, data, and output organization
- `compatibility_wrapper_migration.md` — record of legacy `src.*` wrapper removal
- `audit/` — corpus completeness, authorship, publication-year, topic, and prior-corpus audit reports

## Project structure

```text
.
├── main.py                    # Streamlit application
├── requirements.txt           # Python dependencies
├── data/
│   ├── corpus_v1/             # Current versioned corpus artifacts
│   ├── corpus_metadata.json   # Earlier/root-level corpus artifact, if present
│   ├── eval_dataset.csv       # Evaluation questions and references
│   └── gold_standard/         # Pilot evidence annotations
├── docs/                      # Evidence schema, audits, guidelines, and reports
├── prompt/                    # Answer-generation prompt
├── configs/                   # Shared benchmark configuration
├── requirements/              # Runtime and development dependency groups
├── tests/                     # Unit and integration tests
├── scripts/                   # Organized corpus, benchmark, and annotation entry points
├── pyproject.toml             # Package and tooling metadata
└── src/
    └── biomedical_evidence_engine/
        ├── app/               # Application pipeline
        ├── config/            # Shared Python configuration
        ├── corpus/            # Corpus loading and ingestion interfaces
        ├── evaluation/        # Evaluation package namespace
        └── retrieval/         # Retrieval implementations
```

## Notes

- Answers are evidence-grounded summaries, not medical advice or a substitute for clinical review.
- Corpus rebuilding can change the retrieved evidence as PubMed records and parsing results change.
- The FAISS loader enables LangChain dangerous deserialization for trusted local project artifacts only.
- Keep `.env` out of version control and never commit API keys.
