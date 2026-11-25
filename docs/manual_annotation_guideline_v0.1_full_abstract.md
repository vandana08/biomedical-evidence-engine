# Manual Evidence Annotation Guidelines — Draft v0.1

**Project:** Biomedical Literature Evidence Extraction & Curation System  
**Purpose:** Produce a reproducible, human-reviewed reference set for evaluating evidence extraction.  
**Status:** Updated for full-abstract annotation; based on the 17-record pilot.  
**Schema:** Evidence Schema v0.1. Do not silently change schema fields or controlled vocabularies during annotation.

## 1. Unit of annotation

One evidence record represents **one specific biomarker (or explicitly defined biomarker combination)–relationship–outcome claim in a defined population and, where relevant, treatment context**. Each record must be supported by an exact sentence or the minimum set of adjacent sentences needed to establish the claim.

- Create separate records when a paper reports materially distinct findings, such as different biomarker subgroups, relationships, or treatment comparisons.
- A biomarker combination may remain in one record when the source reports it as a combined finding and does not provide independent effects for its components. Do not split a combined finding into separate biomarker records without source support.
- Multiple outcome endpoints may remain in one record when the source reports them together as a single combined finding and does not provide separable endpoint-specific results. When the source reports distinct endpoint-specific results, separate records are preferred.
- Keep records separate when the direction or comparator differs across biomarker subgroups.
- Do not create a record for a biomarker merely because it is named in the abstract. There must be a specific supported finding.
- Multiple records from one paper should share the same PMID when available.

## 2. Abstract scope, evidence text, and provenance

### 2.1 Abstract scope

- The **entire abstract** is in scope for identifying and contextualizing evidence claims. This includes all available sections: Introduction (or Background), Methods, Results, and Conclusion.
- Do not restrict annotation or evidence extraction to the Results section alone. Different sections may contribute different information: for example, Methods may establish study design, population, or treatment context, while Results may report the finding.
- Use information from any abstract section only for what it explicitly supports. Do not treat background statements as study findings or infer a result from the study objective or methods.
- A conclusion statement may help identify or contextualize a reported claim, but do not use it to infer an unstated subgroup, endpoint, comparator, effect estimate, or statistical result. If the abstract's conclusion makes a claim but the supporting result is not available in the abstract, preserve the limitation and flag the record for review rather than adding unsupported detail.
- Preserve the complete structured abstract during corpus ingestion, including section labels where supplied by PubMed. If the abstract is unstructured, retain the complete available abstract text.

### 2.2 Evidence text and provenance

- `evidence_text` must contain the minimum amount of verbatim source text needed to fully support the annotated claim. The fact that the full abstract is in scope does **not** mean the entire abstract should be copied into `evidence_text`.
- Use one exact sentence by default. Multiple adjacent sentences are allowed when a single sentence is insufficient to establish the claim or its necessary context. This may include adjacent sentences that provide context across abstract sections; retain their original wording and order.
- Do not paraphrase, normalize, or combine non-adjacent fragments into a fabricated sentence.
- Preserve numbers, units, confidence intervals, p-values, endpoint names, and uncertainty exactly as reported.
- Do not infer facts absent from the supplied source.
- Do not insert section headings or explanatory text into `evidence_text` if they are not part of the source sentence. When section provenance is important, identify the relevant section in `annotation_notes`.
- If a claim is supported but an important field is not reported or cannot be determined, retain the record, use `Unknown` for that field, and explain the limitation in `annotation_notes`. Use `N/A` when the field does not apply (for example, trial phase for a non-trial study).
- Do not invent a PMID. Leave it blank if unavailable.
- A dedicated `source_section` field (e.g., Introduction, Methods, Results, Conclusion) is deferred for consideration in a later schema version; it is not part of v0.1.

## 3. Biomarker and factor

- Record the biomarker using the most specific name and terminology stated in the source (e.g., EGFR C797S, PD-L1 expression, hs-cTnT). Do not silently replace the source term with a normalized synonym.
- Use the closest applicable `biomarker_type` from the current schema. If the type cannot be determined from the source, use `Unknown`.
- Preserve mutation identity, subtype distinctions, and expression level/category when explicitly reported.
- Do not infer an individual biomarker effect from a collective statement about several biomarkers.
- Clinical characteristics such as ECOG performance status, age, smoking status, disease stage, and comorbidities are not molecular biomarkers. Do not classify them as mutations, proteins, or expression markers.
- The project should support clinical factors separately from molecular biomarkers. A future schema version should introduce a `factor_type` field (for example, Molecular biomarker, Clinical factor, Treatment/exposure, Other, Unknown) or an equivalent explicit distinction. Until that schema change is approved, flag clinical-factor findings in `annotation_notes` rather than forcing them into the molecular biomarker fields.

## 4. Relationship labels

Use one primary relationship label per evidence record. Choose the most specific label directly supported by the claim; do not assign multiple labels to the same record. If a claim appears to fit more than one category, use the most specific applicable category and explain the ambiguity in `annotation_notes`.

- **Prognostic:** The biomarker is associated with the likelihood or course of a clinical outcome in a defined disease/population, without evidence that the association represents differential benefit from a particular treatment.
- **Predictive:** The biomarker identifies differential relative benefit or outcome from one treatment versus another. Require a treatment comparison across biomarker groups or a biomarker-by-treatment interaction (or equivalent evidence of differential treatment effect). An association observed only within a single treatment group is not sufficient by itself.
- **Resistance:** The biomarker or its change directly identifies, describes, or is associated with a treatment-resistance mechanism or phenotype. Prefer Resistance over a broader Prognostic label when the claim directly concerns resistance.
- **Response:** The source reports an observed response or treatment outcome, but the evidence does not establish differential treatment benefit across biomarker groups or a treatment-by-biomarker interaction.
- **Monitoring:** The biomarker is measured serially or used to track disease/treatment status over time. Do not imply clinical validation, clinical utility, or a decision threshold unless reported.
- **Diagnostic:** The source evaluates the biomarker for identifying or detecting a disease/state. Do not use Diagnostic for a simple association with an already identified condition when diagnostic performance is not evaluated.
- **Association:** The source reports a biomarker–phenotype or biomarker–outcome association that does not meet the operational definition of Prognostic, Predictive, Resistance, Response, Monitoring, or Diagnostic.
- **Other:** Use when the claim does not fit the defined categories.
- **Unknown:** Use when the relationship cannot be determined from the available evidence. Explain the uncertainty in `annotation_notes`.

For overlapping concepts, assign one primary relationship using the most specific supported category. For example, a biomarker directly linked to acquired resistance should be labeled Resistance rather than both Resistance and Prognostic. A biomarker associated with cognitive impairment, without diagnostic performance or a time-to-event prognostic analysis, may be labeled Association.

## 5. Direction

Current labels: Positive, Negative, Neutral, Unclear. Direction must be interpreted relative to the primary relationship being annotated, not from biomarker level alone.

- **Prognostic:** Positive = associated with a favorable clinical outcome; Negative = associated with an unfavorable clinical outcome.
- **Association:** Assign direction based on whether the associated phenotype or outcome is favorable or unfavorable. Do not use an increase/decrease in biomarker level alone to determine direction unless that change itself is the defined outcome.
- **Resistance:** Negative = associated with a more unfavorable resistance phenotype or worse treatment durability/outcome. Positive may be used only when the source supports a favorable resistance-related association. Use Unclear when a resistance alteration is merely detected and no clinical or phenotypic direction is established.
- **Predictive:** State the therapy of interest and comparator explicitly. Positive = the biomarker subgroup has greater relative benefit from the named therapy; Negative = the subgroup has less benefit from the named therapy relative to the comparator. Do not assign direction without identifying the treatment reference.
- **Neutral:** Use only when the source explicitly reports no statistically significant association or difference for the specified endpoint. Do not interpret Neutral as proof of equivalence or absence of a clinically meaningful effect.
- **Unclear:** Use when direction cannot be established from the reported result, evidence is incomplete, or a non-significant trend does not establish a reliable direction.
- A non-significant result is not proof of equivalence or absence of an effect.
- For treatment efficacy, do not label a biomarker–outcome association Positive/Negative without stating the reference treatment where relevant.

## 6. Evidence type, setting, and trial phase

- `evidence_type` describes the design/source supporting the individual evidence claim, not a single overall design assigned to every record from the publication.
- `evidence_setting` describes where the evidence for that claim was generated (e.g., human patients, cell models, xenograft models).
- `trial_phase` applies only to clinical trial evidence. Use the reported phase when available and `Unknown` when a clinical trial is mentioned but its phase is not reported. Use `N/A` for non-clinical-trial evidence.
- When a paper reports distinct preclinical and clinical findings, create separate evidence records and assign each its own appropriate `evidence_type` and `evidence_setting`.
- If a paper combines cohorts or a trial cohort and an observational cohort, annotate the design supporting the particular claim when the abstract makes this clear. Otherwise note the mixed design and flag for review.
- For evidence syntheses, use Systematic review or Meta-analysis as appropriate to the source claim; do not replace it with the designs of the underlying included studies.
- Use `Unknown` rather than guessing a study design, evidence setting, or trial phase.

## 7. Population, therapy, comparator, and outcome

- Record the specific population/subgroup that supports the claim, not automatically the entire study enrollment. Include subgroup sample size when reported.
- Preserve disease stage, mutation status, treatment line, and relevant eligibility criteria when stated. Do not infer population characteristics that are not reported.
- Record the therapy of interest and comparator separately when applicable. Use `N/A` for therapy/comparator when the claim is not treatment-specific; use `Unknown` when treatment context is relevant but not reported.
- A dedicated `comparator` field is proposed for a future schema version; it is not part of v0.1. Until then, record comparator information in the existing therapy field or annotation notes without obscuring which treatment is the reference.
- Preserve endpoint names and terminology as stated in the source, including abbreviations (e.g., RFS, DFS, PFS, OS, ORR, DCR). Do not silently normalize or merge clinically distinct endpoints.
- Multiple endpoints may remain together in one record when the source reports them as one combined finding and does not provide separable endpoint-specific results, consistent with Section 1. When distinct endpoint-specific results are reported, separate records are preferred.

## 8. Statistical findings and uncertainty

- Record effect estimates, confidence intervals, p-values, units, and sample sizes in the exact evidence sentence where available.
- Do not infer statistical significance from wording such as “trend.”
- A confidence interval crossing the null value and a non-significant p-value should not be described as a confirmed association.
- Do not infer causation from observational associations.
- Record limitations such as small subgroup size, missing sample size, low GRADE certainty, or absent effect estimates in `annotation_notes`.

## 9. Measurement method

- Record the method in notes when explicitly stated (e.g., tumor NGS, plasma cfDNA genotyping, immunohistochemistry / TPS).
- Do not infer a method from the biomarker name.
- A dedicated `measurement_method` field is a candidate for a later schema version, not part of v0.1.

## 10. Review flags

Flag a record for adjudication when:
- relationship label is ambiguous (especially Predictive vs Response vs Prognostic);
- direction depends on an unstated comparator;
- multiple endpoints are grouped;
- multiple cohorts/designs contribute to a claim;
- a clinical factor is being represented in a biomarker-oriented schema;
- a finding is mentioned without individual effect estimates;
- evidence text requires context beyond one sentence or uses sentences from more than one abstract section;
- a controlled-vocabulary value is missing.

## 11. Annotation quality checklist

Before accepting a record, confirm:

1. Does it represent one identifiable claim?
2. Is the biomarker/factor explicitly stated?
3. Is the relationship label supported by the study design and reported analysis?
4. Is direction justified and, for predictive claims, tied to a named therapy/comparator?
5. Is the outcome endpoint named precisely?
6. Does the population reflect the subgroup in which the finding was observed?
7. Is the entire available abstract in scope, and have relevant context from Introduction/Background, Methods, Results, and Conclusion been considered without treating background or methods as findings?
8. Is `evidence_text` copied exactly from the source and limited to the minimum sufficient verbatim text?
9. Are missing details marked Unknown/N/A rather than guessed?
10. Are limitations and ambiguities documented?
11. Can another annotator reproduce the same interpretation from the evidence text and notes?

## 12. Open decisions for schema v0.2

Do not change v0.1 until these decisions are approved:

- Add a general `Association` relationship category and define its boundary with Diagnostic/Prognostic.
- Add `comparator` for predictive findings.
- Add `factor_type` or generalize `biomarker` to represent clinical factors.
- Decide whether `measurement_method` and `source_cohort` need dedicated fields.
- Decide whether structured effect estimate fields (estimate, CI, p-value, unit, reference group) are required.
- Decide whether `study_id` is needed in addition to PMID.


## 13. Version history

- **v0.1 (updated):** Clarified that the complete abstract is in scope (Introduction/Background, Methods, Results, and Conclusion); specified how to use section context, preserve verbatim evidence text, and document section provenance without adding a v0.1 schema field.
