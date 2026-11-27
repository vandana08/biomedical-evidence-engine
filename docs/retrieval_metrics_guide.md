# Retrieval Metrics Guide

This guide explains the metrics used in the PMID-level retrieval benchmark.
For Precision@5, pooled Recall@5, and MRR, relevance labels `1` and `2` are
treated as relevant. nDCG@5 uses the graded labels directly:

- `2` — directly answers the question with relevant evidence
- `1` — provides supporting or related evidence
- `0` — does not meaningfully address the question

All calculations are performed at the PMID level. If several chunks belong to
the same paper, the paper is counted once and assigned its first paper-level
rank.

## Precision@5

### Formula

```text
Precision@5 = relevant papers in the first 5 results
              ----------------------------------------
              papers returned in the first 5 results
```

Labels `1` and `2` are relevant for this metric.

### Simple example

Suppose the first five results have labels:

```text
2, 1, 0, 0, 1
```

Three of five papers are relevant, so:

```text
Precision@5 = 3 / 5 = 0.60
```

### Significance

Precision@5 estimates how many useful papers a clinician or researcher is
likely to see immediately, without reviewing many irrelevant results.

## Pooled Recall@5

### Formula

```text
Pooled Recall@5 = relevant papers from this method in the first 5 results
                  ------------------------------------------------------
                  all relevant papers in the judged pooled candidate set
```

The denominator is built from the union of candidates retrieved by all
methods and manually judged for that question.

### Simple example

Suppose the judged pool contains eight relevant papers. A method retrieves
three of them in its first five results:

```text
Pooled Recall@5 = 3 / 8 = 0.375
```

### Significance

This measures how much of the known relevant evidence the method surfaces
early. It is called *pooled* recall because it is not recall over every paper
in the 957-paper corpus. A relevant paper missed by every method is absent
from the judged pool and cannot contribute to the denominator.

## Mean Reciprocal Rank (MRR)

### Formula

For each question:

```text
RR = 1 / rank of the first relevant paper
```

Across questions:

```text
MRR = (RR for question 1 + RR for question 2 + ... + RR for question N) / N
```

The benchmark calculates MRR over the available PMID-ranked results, up to the
top 10 retrieved papers.

### Simple example

If the first relevant paper appears at rank 2:

```text
RR = 1 / 2 = 0.50
```

If five questions have reciprocal ranks `1.00, 0.50, 0.33, 1.00, 0.25`:

```text
MRR = (1.00 + 0.50 + 0.33 + 1.00 + 0.25) / 5 = 0.616
```

### Significance

MRR measures how quickly a user encounters the first relevant paper. It is
especially useful when the first good result matters more than the complete
ordering of the remaining results.

## nDCG@5

nDCG@5 evaluates both relevance quality and ranking position. Unlike the
binary metrics, it distinguishes directly relevant papers from supporting
context.

### Step 1: Discounted cumulative gain

```text
DCG@5 = sum for positions i = 1 to 5 of:
        (2^relevance_at_position_i - 1) / log2(i + 1)
```

The gain for each label is:

| Label | Gain: `2^label - 1` |
|---:|---:|
| 0 | 0 |
| 1 | 1 |
| 2 | 3 |

### Step 2: Ideal DCG

Sort all judged papers for the question from highest label to lowest, take the
best five, and calculate DCG using that ideal ordering:

```text
IDCG@5 = DCG@5 for the ideal ordering of the judged papers
```

### Step 3: Normalize

```text
nDCG@5 = DCG@5 / IDCG@5
```

The result ranges from 0 to 1, where 1 means the method produced the ideal
graded ordering for the first five positions.

### Simple example

Suppose the top five labels are:

```text
2, 1, 0, 1, 0
```

Then:

```text
DCG@5 = 3/log2(2) + 1/log2(3) + 0/log2(4)
        + 1/log2(5) + 0/log2(6)
      ≈ 4.062
```

If the ideal top-five labels for the judged pool are:

```text
2, 2, 1, 1, 0
```

then:

```text
IDCG@5 ≈ 5.823
nDCG@5 ≈ 4.062 / 5.823 ≈ 0.697
```

### Significance

nDCG@5 rewards placing directly relevant papers near the top while still
giving credit to useful supporting papers. It is generally more informative
than binary Precision@5 when annotation has meaningful relevance grades.

## Jaccard similarity

Jaccard similarity compares the overlap between two sets of retrieved papers
or chunks.

### Formula

```text
Jaccard(A, B) = number of items in both A and B
                --------------------------------
                number of items in A or B
```

The benchmark reports Jaccard similarity at both the chunk level and the PMID
level. PMID-level Jaccard is the preferred measure for comparing papers.

### Simple example

Suppose method A retrieves:

```text
{P1, P2, P3}
```

and method B retrieves:

```text
{P2, P3, P4}
```

The intersection has two papers and the union has four:

```text
Jaccard(A, B) = 2 / 4 = 0.50
```

### Significance

Jaccard similarity shows how similarly two retrieval methods select evidence.
A high value means their candidate sets are similar; a low value means they
surface substantially different papers. It measures agreement, not which
method is more medically relevant.

## Interpretation cautions

- Metrics are macro-averaged across the five questions so each question has
  equal weight.
- Latency is reported separately from retrieval quality.
- Pooled recall is limited by the judged candidate pool.
- Metric differences should be interpreted together with question-level error
  analysis and expert review.
