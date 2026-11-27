# Retrieval Benchmark Evaluation

## Run provenance

- Benchmark run: `retrieval_benchmark_20261126_111147`
- Corpus: `EGFR-NSCLC v1.0`
- Corpus size: 957 unique PMIDs and 2,637 chunks
- Questions: 5
- Evaluation unit: PMID, not chunk
- Relevance labels: `0`, `1`, and `2`
- Binary relevance: labels `1` and `2`
- Pooled recall denominator: all relevant PMIDs in the judged union of retrieved candidates

The source outputs are under
`outputs/retrieval_benchmark_20261126_111147/evaluation/`.

## Initial method comparison

| Method | Precision@5 | Pooled Recall@5 | MRR | nDCG@5 | Mean latency (ms) | Median latency (ms) |
|---|---:|---:|---:|---:|---:|---:|
| BM25 | 0.7600 | 0.2194 | 0.7667 | 0.5150 | 20.99 | 18.16 |
| Dense | 1.0000 | 0.2889 | 1.0000 | 0.7912 | 860.04 | 389.00 |
| Hybrid RRF | 0.8800 | 0.2565 | 1.0000 | 0.7208 | 363.73 | 350.26 |
| Hybrid + CrossEncoder | 1.0000 | 0.2889 | 1.0000 | 0.7742 | 2543.54 | 2568.42 |

## Findings

Dense retrieval achieved the strongest overall ranking performance in this
initial benchmark. It matched the reranking hybrid on binary relevance
metrics and had higher nDCG@5, while using substantially less latency.

The CrossEncoder hybrid achieved the same Precision@5, pooled Recall@5, and
MRR as dense retrieval, but its mean latency was approximately 2.5 seconds
compared with approximately 0.86 seconds for dense retrieval.

BM25 was the fastest baseline at approximately 21 ms. Hybrid RRF provided an
intermediate latency of approximately 364 ms and stronger results than BM25 on
all reported quality metrics except that it remained below dense retrieval.

## Limitations

This is an initial five-question benchmark. Pooled Recall@5 is not true
corpus-wide recall: relevant papers missed by every retrieval method are not
included in the judged pool. The results should therefore guide further
evaluation rather than serve as a definitive retrieval-strategy selection.
Additional questions, independently reviewed labels, and repeated runs would
make the comparison more robust.

## Detailed outputs

- `method_metrics.csv` — macro-averaged method comparison
- `question_metrics.csv` — question-level metrics
- `latency_summary.csv` — method/question latency
- `top5_predictions.csv` — PMID-level top-five predictions and labels
- `error_analysis.csv` — false positives and relevant papers ranked below five
