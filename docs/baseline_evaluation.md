# Baseline Evaluation Report

**Project:** Biomedical Literature Evidence Extraction & Curation System  
**Corpus focus:** EGFR-mutant non-small cell lung cancer (NSCLC)  
**Evaluation stage:** Initial retrieval-and-generation baseline  
**Source:** `baseline_questions.docx`  
**Status:** Baseline observations recorded; not a formal gold-standard accuracy evaluation

## 1. Purpose

This report records the initial system behaviour across five representative biomedical questions. It captures the generated answers, retrieved PubMed evidence, and reported latency measurements so that later retrieval and answer-generation changes can be compared against a documented baseline.

The five questions cover osimertinib resistance, EGFR T790M, osimertinib response, progression-free survival (PFS), and EGFR C797S-mediated resistance.

## 2. Baseline questions and latency

Latency values below are transcribed from the supplied baseline output. All values are in milliseconds.

| # | Baseline question | Total latency (ms) | Retrieval (ms) | Generation (ms) |
|---|---|---:|---:|---:|
| 1 | What EGFR mutations are associated with resistance to osimertinib in NSCLC? | 13,161 | 3,890 | 3,165 |
| 2 | What is the role of EGFR T790M in resistance to EGFR tyrosine kinase inhibitors? | 10,081 | 2,598 | 3,036 |
| 3 | Which EGFR mutations are associated with response to osimertinib? | 8,992 | 2,373 | 1,963 |
| 4 | What biomarkers are associated with progression-free survival in EGFR-mutant NSCLC? | 10,567 | 3,615 | 2,279 |
| 5 | What evidence is available for EGFR C797S-mediated resistance? | 9,423 | 1,751 | 2,795 |
| | **Mean** | **10,444.8** | **2,845.4** | **2,647.6** |

The reported total latency is retained as provided by the source. It is not assumed to equal retrieval plus generation latency; the source does not explain the timing boundaries or any additional overhead.

## 3. Retrieval and answer observations

### Question 1 — EGFR mutations associated with osimertinib resistance

The generated answer identified EGFR C797S, loss of T790M, NCOA4-RET fusion, TP53 mutation, and other co-alterations.

The retrieved abstracts included:
- A case report describing acquired EGFR C797S in the absence of T790M after osimertinib.
- A case report describing NCOA4-RET fusion alongside TP53 co-mutation after progression on osimertinib.
- A systematic review describing several resistance mechanisms and associations with worse PFS.

**Baseline observation:** The answer captures several mechanisms represented in the retrieved material. However, it groups point mutations, co-mutations, and gene fusions under the broad wording of “mutations.” A more structured answer should distinguish EGFR on-target mutations from bypass alterations, fusions, and co-mutations, and connect each claim to its supporting source.

### Question 2 — Role of EGFR T790M in resistance to EGFR TKIs

The generated answer describes T790M as a resistance mechanism that commonly emerges after an initial response to first-generation EGFR TKIs and explains the relevance of third-generation TKIs.

The retrieved abstracts included:
- A study of EGFR T790I, which is not the same alteration as T790M.
- A retrospective study examining T790M after first-generation EGFR-TKI resistance.
- A paper discussing T790M and acquired resistance in lung adenocarcinoma.
- Other retrieved records concerning EGFR-TKI resistance mechanisms.

**Baseline observation:** The answer is broadly aligned with the question, but the retrieved set includes a T790I paper. The system should distinguish closely named but different variants and prioritize evidence specifically about T790M.

### Question 3 — EGFR mutations associated with response to osimertinib

The generated answer identifies activating EGFR mutations, including exon 19 deletion and exon 21 substitution mutations.

The retrieved abstracts included multiple records about osimertinib resistance, C797S, L718Q, and activating EGFR mutations. Several retrieved records did not directly provide evidence comparing response across EGFR mutation subgroups.

**Baseline observation:** There is a relevance mismatch between the response-focused question and several resistance-focused retrieved records. The answer is plausible at a high level, but the supplied retrieval output does not clearly establish the mutation-specific response claim. Retrieval should better distinguish response evidence from resistance evidence.

### Question 4 — Biomarkers associated with PFS in EGFR-mutant NSCLC

The generated answer mentions PD-L1 expression and LKB1 loss. It states that PD-L1 was associated with poor RFS but not PFS in EGFR-mutant patients receiving EGFR-TKIs, while LKB1 loss was associated with worse PFS and OS.

The retrieved abstracts included:
- A PD-L1 study reporting RFS findings and no significant association with PFS, OS, ORR, or DCR in the described post-relapse EGFR-TKI-treated subgroup.
- An LKB1 study reporting an association between LKB1 loss and worse PFS and OS in advanced NSCLC.

**Baseline observation:** This example illustrates the risk of conflating clinical endpoints. RFS, PFS, and OS are distinct outcomes and should not be presented interchangeably. The population supporting each biomarker claim also needs to be stated precisely; the retrieved LKB1 record should not automatically be treated as evidence specific to EGFR-mutant NSCLC without confirming its analysed subgroup.

### Question 5 — Evidence for EGFR C797S-mediated resistance

The generated answer describes C797S as a common acquired resistance mechanism and mentions potential therapeutic strategies, including HS-10375 and JIN-A02.

The retrieved abstracts included:
- A case report describing C797S after osimertinib.
- A case report describing treatment after acquired EGFR 19del/C797S resistance.
- A report of preclinical research and a first-in-human Phase 1 trial of HS-10375.
- A study evaluating JIN-A02 as a potential fourth-generation EGFR-TKI.

**Baseline observation:** The retrieved records provide a mixture of case-level, preclinical, and early clinical evidence. The answer should distinguish established clinical observations from investigational therapeutic approaches and label the evidence type and development stage.

## 4. Cross-query findings

The five examples indicate several areas for improvement:

1. **Retrieval relevance:** Some retrieved records address adjacent topics rather than the precise question, particularly resistance records returned for the osimertinib-response question.
2. **Variant discrimination:** Similar mutation names, such as T790M and T790I, need explicit differentiation.
3. **Endpoint fidelity:** PFS, RFS, and OS must remain separate throughout retrieval and answer synthesis.
4. **Evidence-type separation:** Case reports, retrospective cohorts, systematic reviews, preclinical studies, and early-phase trials should not be presented as equivalent evidence.
5. **Claim-level provenance:** Individual claims should be linked to the specific abstract or source passage that supports them.
6. **Population specificity:** Biomarker findings should retain the patient subgroup and treatment context to which the result applies.
7. **Answer calibration:** The system should avoid presenting a broad conclusion when the retrieved abstracts only provide indirect, incomplete, or subgroup-specific support.

These are qualitative observations from the five supplied examples. They are not measured error rates.

## 5. Baseline latency summary

Across the five questions:

- Mean reported total latency: **10.44 seconds**
- Mean retrieval latency: **2.85 seconds**
- Mean generation latency: **2.65 seconds**

The source reports total latency separately from retrieval and generation latency. Their values should not be added or treated as a complete latency decomposition without confirming how the application measures each stage.

## 6. Evaluation limitations

This baseline is an initial qualitative assessment, not a formal accuracy benchmark.

The supplied document does not provide:
- Gold-standard relevant-document labels for each query.
- Precision, recall, or ranking metrics such as Precision@K, Recall@K, or nDCG.
- Claim-level factuality or citation-support scores.
- A systematic adjudication of whether every generated statement is supported by the retrieved abstracts.
- Repeated latency runs or latency distributions.

The five questions are useful as a fixed regression set, but a larger annotated evaluation set will be needed for robust performance claims.

## 7. Recommended use as the comparison baseline

Keep the five questions unchanged when evaluating subsequent corpus or retrieval changes. For each run, record:

- Retrieved PMIDs and ranking order.
- Whether the retrieved evidence directly addresses the question.
- Whether the answer preserves mutation identity, endpoint, population, therapy, and evidence type.
- Whether each substantive claim is supported by a cited source passage.
- Retrieval, generation, and end-to-end latency using clearly defined timing boundaries.

Compare the new system against this report and the original retrieved outputs. Do not interpret improvements in latency alone as improvements in evidence quality.

---

**Baseline source note:** This report is based on the five question/answer/retrieval examples and latency values in the supplied `baseline_questions.docx`. Qualitative findings are limited to what those examples show. No additional source verification or external literature review was performed for this report.
