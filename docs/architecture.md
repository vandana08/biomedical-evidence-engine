# Project Architecture

```text
corpus ingestion -> persisted corpus artifacts -> retrieval -> evaluation/reports
                                      |
                                      -> Streamlit application
```

Production code lives under `src/biomedical_evidence_engine/`:

- `corpus/` — corpus loading and ingestion interfaces
- `retrieval/` — BM25, dense, RRF, reranked hybrid, and shared utilities
- `app/` — question-answering pipeline
- `config/` — shared benchmark configuration
- `evaluation/` — evaluation package namespace

Operational entry points are grouped under `scripts/`:

- `scripts/corpus/` — build and validate corpus artifacts
- `scripts/benchmarks/` — baseline, retrieval, stability, overlap, and relevance runs
- `scripts/annotation/` — annotation candidate exports

Root-level scripts remain supported command-line entry points, while the
production implementation is owned by the package. Generated benchmark and
evaluation artifacts belong under `outputs/` and should include a metadata
manifest describing the corpus version, questions, methods, parameters, and
timestamps.

Tests are grouped under `tests/unit/` for isolated component checks and
`tests/integration/` for end-to-end orchestration checks.
