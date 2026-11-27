# Latency and Retrieval Stability Methodology

## Measurement scope

Latency is measured after corpus loading, embedding model initialization, and
retriever initialization. It covers only the timed `retrieve_docs()` query
operation. One-time setup and warm-up costs are excluded.

Each retriever receives one untimed warm-up query before the five benchmark
questions are measured. Each question is then executed three times. Three runs
provide an initial estimate only; they do not characterize production tail
latency, long-term variance, or workload effects.

## Stability measures

- **Jaccard@10** measures overlap between the unique top-10 PMID sets across
  repeated runs.
- **Top-5 set consistency** checks whether the same five PMIDs are present.
- **Top-5 order consistency** checks whether those five PMIDs appear in the
  same order.
- **RBO@10** measures rank-sensitive agreement, giving more weight to higher
  positions and handling membership differences. The implementation uses a
  normalized finite-prefix RBO with persistence `p = 0.9`.

Retrieval-set stability and ranking-order stability are separate. Two runs can
return the same papers but order them differently. Jaccard alone would not
detect that difference.

## Running the benchmark

```powershell
python run_retrieval_stability_benchmark.py `
  --output-dir outputs/retrieval_benchmark_<timestamp>/stability
```

Use `--retriever dense` to evaluate only dense retrieval. Outputs include
per-run results, per-question latency, overall latency, pairwise stability,
and a Markdown report.
