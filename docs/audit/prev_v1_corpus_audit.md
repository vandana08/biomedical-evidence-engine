# Corpus Audit — EGFR-NSCLC

**Audit objective:** Assess the structure, completeness, metadata quality and topic coverage of the existing PubMed corpus before developing the biomedical evidence extraction pipeline.

## 1. Corpus Overview

The saved corpus contains 953 LangChain Document records.

| Metric | Result |
|---|---:|
| Total documents | 953 |
| Unique PMIDs | 953 |
| Duplicate PMIDs | 0 |
| Empty document texts | 0 |
| Median text length | 460 characters |
| Mean text length | 503.72 characters |
| Minimum text length | 88 characters |
| Maximum text length | 999 characters |

All 953 records contain the following metadata fields:

- PMID
- Title
- Journal
- Year
- Authors
- Keywords
- Source

**Observation:** The saved corpus contains one document per PMID. The maximum text length of 999 characters is consistent with the configured chunk size of 1,000 characters, but does not independently establish whether text was truncated.

## 2. Chunking and Deduplication Audit

The ingestion pipeline uses `RecursiveCharacterTextSplitter` with:

- Chunk size: 1,000 characters
- Chunk overlap: 200 characters

The corpus builder subsequently deduplicates documents using PMID as the dictionary key.

A diagnostic reproduction using the two PubMed queries produced:

| Metric | Result |
|---|---:|
| Query 1 chunks | 816 |
| Query 2 chunks | 800 |
| Combined chunks | 1,616 |
| Unique PMIDs | 953 |
| Records retained after deduplication | 953 |
| Extra chunk occurrences discarded | 663 |
| Proportion of occurrences discarded | 41.0% |

A total of 464 PMIDs had multiple occurrences in the combined results.

The 663 discarded occurrences comprise:

- 641 extra occurrences within the individual query results.
- 22 additional occurrences caused by overlap between the two queries.

**Finding:** PMID-based deduplication collapses multiple chunks belonging to the same paper into a single document. The dictionary retains the last encountered chunk for each PMID, potentially discarding other relevant sections.

This can remove distinct evidence from the same paper, including methods, results and conclusions.

**Limitation:** These figures come from a fresh PubMed retrieval and are a diagnostic reproduction, not an exact reconstruction of the historical corpus build.

## 3. Abstract Completeness Audit

A sample of 50 PMIDs was selected from the saved corpus. Current PubMed XML records were retrieved and compared against the existing extraction logic.

The current implementation extracts only the first `AbstractText` element.

| Metric | Result |
|---|---:|
| PMIDs sampled | 50 |
| Successfully fetched | 50 |
| Records containing abstracts | 50 |
| Records with multiple sections | 23 (46%) |
| Complete abstract characters | 89,684 |
| Characters retained by current extraction | 55,111 |
| Characters discarded | 34,573 |
| Overall character loss | 38.55% |

**Finding:** The current ingestion implementation discards all abstract sections after the first. Structured sections such as Methods, Results and Conclusions may therefore be missing.

This can remove important biomarker-outcome relationships, treatment context and population details.

**Limitation:** The sample uses the first 50 corpus PMIDs rather than a random sample. The results should not be generalized to the entire corpus without additional sampling. PubMed records were retrieved at the time of this audit and may differ from historical versions.

## 4. Author Metadata Audit

A fresh PubMed retrieval of the two queries identified 977 unique articles.

| Metric | Result |
|---|---:|
| Unique articles inspected | 977 |
| Articles with missing author initials | 4 |
| Potentially skipped articles | 0.41% |

The ingestion code accesses `Initials` whenever `LastName` exists. An article with a last name but no initials can therefore raise an exception and cause the entire article to be skipped.

**Finding:** This is a confirmed ingestion robustness issue, although the observed frequency in this diagnostic was low.

**Limitation:** The 977 articles represent a fresh PubMed retrieval, not necessarily the exact set used to build the saved corpus.

## 5. Publication Year Distribution

| Publication year | Documents |
|---|---:|
| 2021 | 20 |
| 2022 | 119 |
| 2023 | 85 |
| 2024 | 107 |
| 2025 | 519 |
| 2026 | 102 |
| Unknown | 1 |
| **Total** | **953** |

**Observations:**

- 2025 accounts for approximately 54.5% of the corpus.
- 2025 and 2026 together account for approximately 65.2%.
- The corpus is heavily weighted toward recent publications.

This may reflect the search queries, retrieval limits and corpus construction date. It should be considered when assessing temporal coverage and evidence generalizability.

## 6. Topic Distribution

Topic categories were identified using keyword matching against document titles and saved abstract text.

| Topic | Documents | Percentage |
|---|---:|---:|
| Biomarker and mutation | 576 | 60.4% |
| Resistance | 422 | 44.3% |
| Survival and prognosis | 265 | 27.8% |
| Treatment response | 233 | 24.4% |
| Diagnosis and detection | 70 | 7.3% |

**Observations:**

- Biomarker and mutation literature is the most represented category.
- Resistance is also strongly represented.
- Diagnosis and detection is comparatively underrepresented.

**Limitation:** Categories are based on keyword matching and can overlap. These counts are indicative rather than manually validated evidence classifications. Abstract truncation may also affect classification.

## 7. Additional Metadata Observation

The `keywords` metadata field is populated using PubMed MeSH headings (`MeshHeadingList`), rather than author-supplied keywords.

This should be documented accurately in downstream processing.

## 8. Key Findings and Priorities

| Finding | Impact | Priority |
|---|---|---|
| Multiple chunks collapsed by PMID deduplication | High | High |
| Structured abstracts truncated | High | High |
| Missing author initials can skip articles | Low observed frequency | Medium |
| Strong publication-year concentration | Coverage consideration | Medium |
| Diagnosis/detection comparatively underrepresented | Coverage consideration | Medium |
| MeSH terms stored as keywords | Metadata clarity | Low |

## 9. Overall Assessment

The existing corpus provides a useful starting point for a biomedical evidence extraction system:

- 953 unique PubMed records.
- Complete presence of the inspected metadata fields.
- No empty document texts.
- Strong coverage of biomarker and resistance-related literature.

However, the current ingestion pipeline has two important limitations that directly affect evidence completeness:

1. Multiple chunks belonging to the same PMID can be collapsed during deduplication.
2. Only the first section of structured PubMed abstracts is retained.

These issues can remove important scientific evidence even when the relevant paper has been retrieved.

The corpus is suitable as a baseline for further development, but its current representation should not be treated as a complete or fully reliable evidence source.

## 10. Next Steps

1. Finalize an evidence schema for biomarker-level evidence records.
2. Manually annotate a small gold-standard set of evidence statements.
3. Define annotation guidelines for evidence type, relationship, direction and outcome.
4. Use the gold-standard annotations to evaluate extraction quality and evidence traceability.

**Audit status:** Initial corpus audit completed. Findings documented for the next stage of evidence extraction development.