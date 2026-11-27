# Compatibility Wrapper Removal Record

The legacy `src/*.py` module wrappers have been removed. Production imports now
use the package implementation under `src/biomedical_evidence_engine/`.

## Current package-owned implementations

- `biomedical_evidence_engine.corpus.ingestor`
- `biomedical_evidence_engine.corpus.loader`
- `biomedical_evidence_engine.retrieval.bm25`
- `biomedical_evidence_engine.retrieval.dense`
- `biomedical_evidence_engine.retrieval.hybrid_rrf`
- `biomedical_evidence_engine.retrieval.hybrid_reranked`
- `biomedical_evidence_engine.retrieval.reranker`
- `biomedical_evidence_engine.retrieval.utils`
- `biomedical_evidence_engine.app.pipeline`
- `biomedical_evidence_engine.evaluation.ragas_evaluation`
- `biomedical_evidence_engine.evaluation.testset`

## Completed removal steps

1. Searched the repository for imports beginning with
   `src.`.
2. Replaced internal imports with `biomedical_evidence_engine.*` imports.
3. Ran the import audit, compilation, and retrieval smoke checks.
4. Prepared corpus validation, retrieval, annotation, relevance, and stability
   smoke checks.
5. Confirmed no source or test file references a legacy `src.` import.
6. Removed the thin wrappers and `src/__init__.py`.
7. Kept the package import audit as a release check.

External notebooks or downstream integrations that still import paths such as
`src.hybrid_retriever` must migrate to the package paths before upgrading.
