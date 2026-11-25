# Biomedical Evidence Schema v0.1

**Project:** Biomedical Literature Evidence Extraction & Curation
System\
**Version:** 0.1\
**Status:** Updated for alignment with Manual Evidence Annotation
Guidelines v0.1\
**Purpose:** Structured manual annotation of biomarker-related evidence
from biomedical literature.

## 1. Objective and unit of annotation

One evidence record represents one specific biomarker (or explicitly
defined biomarker combination)--relationship--outcome claim in a defined
population and, where relevant, treatment context. Each record must be
supported by the minimum amount of exact source text needed to establish
the claim.

A single publication may generate multiple evidence records. Distinct
biomarker subgroups, relationships, treatment comparisons, or separable
endpoint-specific findings should be represented as separate records. A
biomarker combination or multiple endpoints may remain together when the
source reports them as one combined finding and does not provide
independent or separable results.

## 2. Evidence record fields

  ----------------------------------------------------------------------------------------------------
  Field                   Description             Example / guidance
  ----------------------- ----------------------- ----------------------------------------------------
  `evidence_id`           Unique identifier for   `EV001`
                          the evidence record     

  `pmid`                  PubMed identifier of    `12345678`; leave blank if unavailable; do not
                          the source publication  invent

  `biomarker`             Biomarker or molecular  `EGFR C797S`; do not silently normalize
                          alteration, using the   
                          source terminology      

  `biomarker_type`        Type of biomarker       `Mutation`

  `cancer_type`           Cancer classification   `NSCLC`

  `cancer_subtype`        More specific cancer    `EGFR-mutant lung adenocarcinoma`
                          subtype                 

  `therapy`               Treatment relevant to   `Osimertinib`; use `N/A` when not treatment-specific
                          the claim               and `Unknown` when relevant but unreported

  `relationship`          Primary type of         `Resistance`
                          biomarker--outcome      
                          relationship            

  `direction`             Direction of the        `Negative`
                          association relative to 
                          the annotated           
                          relationship and        
                          outcome                 

  `outcome`               Specific clinical or    `Progression-free survival (PFS)`
                          biological outcome,     
                          using the source        
                          terminology             

  `evidence_type`         Study design or         `Retrospective cohort`
                          evidence category       
                          supporting this         
                          particular claim        

  `evidence_setting`      Setting in which the    `Human patients`; `Cell models`; `Xenograft models`
                          evidence for this claim 
                          was generated           

  `trial_phase`           Clinical trial phase,   `Phase III`; `Unknown`; `N/A`
                          when applicable         

  `population`            Specific population or  `Patients with EGFR-mutant NSCLC`; include subgroup
                          subgroup supporting the size when reported
                          claim                   

  `evidence_text`         Exact source text       Verbatim sentence or minimum set of adjacent
                          supporting the          sentences
                          annotated claim         

  `annotation_notes`      Additional context,     `Non-significant trend; direction not established`
                          ambiguity, uncertainty, 
                          limitations, and review 
                          notes                   
  ----------------------------------------------------------------------------------------------------

### Field conventions

-   Use `Unknown` when a field is relevant but cannot be determined from
    the source.
-   Use `N/A` when a field does not apply.
-   Do not infer missing information or silently normalize source
    terminology.
-   For clinical factors (e.g., ECOG performance status, age, smoking
    status, stage, or comorbidities), do not force the factor into
    molecular biomarker fields. Flag the record in `annotation_notes`. A
    separate `factor_type` field is deferred to a future schema version.
-   A biomarker combination may be retained in one record when the
    source reports it as one combined finding. Because v0.1 has a single
    `biomarker_type` field, use one type only when all biomarkers in the
    combination share that type. If a combination contains different
    biomarker types, document the limitation in `annotation_notes`;
    support for multiple biomarker types is deferred to a future version.
-   `comparator` is not a separate field in v0.1. When relevant,
    identify the comparator in `evidence_text` and/or
    `annotation_notes`.
-   Evidence certainty (including GRADE, when reported) is recorded in
    `annotation_notes`; there is no dedicated field in v0.1.
-   Preserve effect estimates, confidence intervals, p-values, units,
    and sample sizes in `evidence_text` when reported. Do not create
    separate structured statistical fields in v0.1.
-   If statistical details are missing but the claim is otherwise
    supported, retain the record and document the missing details in
    `annotation_notes`.

## 3. Controlled vocabularies

### 3.1 Biomarker type

-   Mutation
-   Fusion
-   Amplification
-   Deletion
-   Expression
-   Methylation
-   Protein
-   Other
-   Unknown

Use the closest applicable category supported by the source. Preserve
the specific biomarker name and subtype in `biomarker`.

### 3.2 Relationship

Use one primary relationship label per record. Select the most specific
category directly supported by the claim.

-   **Resistance:** The biomarker or its change directly identifies,
    describes, or is associated with a treatment-resistance mechanism or
    phenotype.
-   **Response:** The source reports an observed response or treatment
    outcome, but the evidence does not establish differential treatment
    benefit across biomarker groups or a treatment-by-biomarker
    interaction.
-   **Prognostic:** The biomarker is associated with the likelihood or
    course of a clinical outcome in a defined disease/population,
    without evidence that the association represents differential
    benefit from a particular treatment.
-   **Predictive:** The biomarker identifies differential relative
    benefit or outcome from one treatment versus another. Require a
    treatment comparison across biomarker groups or a
    biomarker-by-treatment interaction (or equivalent evidence of
    differential treatment effect). An association observed only within
    a single treatment group is not sufficient by itself.
-   **Monitoring:** The biomarker is measured serially or used to track
    disease/treatment status over time. Do not imply clinical
    validation, clinical utility, or a decision threshold unless
    reported.
-   **Diagnostic:** The source evaluates the biomarker for identifying
    or detecting a disease/state. Do not use Diagnostic for a simple
    association with an already identified condition when diagnostic
    performance is not evaluated.
-   **Association:** The source reports a biomarker--phenotype or
    biomarker--outcome association that does not meet the operational
    definition of Prognostic, Predictive, Resistance, Response,
    Monitoring, or Diagnostic.
-   **Other:** The claim does not fit the defined categories.
-   **Unknown:** The relationship cannot be determined from the
    available evidence; explain the uncertainty in `annotation_notes`.

For overlapping concepts, assign one primary label using the most
specific supported category. Prefer Resistance over a broader Prognostic
label when the claim directly concerns resistance. Do not assign
multiple relationship labels to one record.

### 3.3 Direction

The `direction` field describes the direction of the biomarker's
association with the reported clinical or biological outcome. It does
not describe treatment effectiveness in isolation.

-   **Positive:** Associated with a favorable outcome or phenotype,
    relative to the annotated relationship.
-   **Negative:** Associated with an unfavorable outcome or phenotype,
    relative to the annotated relationship.
-   **Neutral:** The source explicitly reports no statistically
    significant association or difference for the specified endpoint.
    Neutral does not establish equivalence or absence of a clinically
    meaningful effect.
-   **Unclear:** Direction cannot be established from the reported
    result, evidence is incomplete, or a non-significant trend does not
    establish a reliable direction.

Relationship-specific interpretation:

-   **Prognostic:** Positive = associated with a favorable clinical
    outcome; Negative = associated with an unfavorable clinical outcome.
-   **Association:** Base direction on whether the associated phenotype
    or outcome is favorable or unfavorable. Do not use an
    increase/decrease in biomarker level alone unless that change itself
    is the defined outcome.
-   **Resistance:** Negative = associated with a more unfavorable
    resistance phenotype or worse treatment durability/outcome. Positive
    requires source support for a favorable resistance-related
    association. Use Unclear when an alteration is merely detected and
    no clinical or phenotypic direction is established.
-   **Predictive:** State the therapy of interest and comparator
    explicitly in the evidence context. Positive = the biomarker
    subgroup has greater relative benefit from the named therapy;
    Negative = it has less benefit from the named therapy relative to
    the comparator. Do not assign direction without identifying the
    treatment reference.
-   **Response:** Base direction on the reported response or treatment
    outcome and preserve the treatment context. Positive = favorable
    response/outcome (e.g., tumor regression or partial response);
    Negative = unfavorable response/outcome (e.g., progressive disease
    or lack of response); Neutral = the source explicitly reports no
    statistically significant response difference for the specified
    endpoint; Unclear = the direction cannot be established from the
    available information.
-   **Monitoring / Diagnostic:** Use direction only when the source
    supports a favorable/unfavorable direction for the specific
    monitored or diagnostic outcome; otherwise use Unclear as
    appropriate.

A non-significant result is not proof of equivalence or absence of an
effect. Do not convert a non-significant trend into an established
Positive or Negative association.

### 3.4 Evidence type

`evidence_type` describes the design/source supporting the individual
evidence claim, not necessarily the overall publication. Use the most
specific category supported by the source.

**Clinical evidence** - Randomized clinical trial - Early-phase clinical
trial - Prospective cohort - Retrospective cohort - Observational
study - Case report - Case series

**Preclinical evidence** - Preclinical --- in vitro - Preclinical --- in
vivo - Preclinical --- in vitro and in vivo

**Evidence synthesis** - Systematic review - Meta-analysis

**Other** - Other - Unknown

For a mixed publication, create separate records for distinct
preclinical and clinical findings when they support different claims.
Assign the evidence type that supports the particular claim. If the
design supporting a claim cannot be determined, use `Unknown` and
explain the issue in `annotation_notes`.

### 3.5 Evidence setting

Describes where the evidence supporting the claim was generated,
independently of study design. Use this strict controlled vocabulary
for v0.1:

-   Human patients
-   Cell models
-   Animal models
-   Xenograft models
-   Patient-derived models
-   In vitro and in vivo models
-   Other
-   Unknown

Choose the most specific applicable category supported by the source.
Use `Other` when the setting is explicitly described but is not covered
by the listed categories; explain the setting in `annotation_notes`.
Use `Unknown` when the setting cannot be determined from the source.
Do not introduce new evidence-setting labels in v0.1.

When one claim is supported by more than one setting, record all
applicable controlled-vocabulary values in a single field, separated
by semicolons (for example, `Cell models; Xenograft models`). Do not
infer a setting.

### 3.6 Trial phase

Record the clinical trial phase when applicable.

-   Phase I
-   Phase I/II
-   Phase II
-   Phase III
-   Phase IV
-   Other specified phase
-   Unknown
-   N/A

Use `Unknown` when clinical trial evidence is described but the phase is
not stated. Use `N/A` for non-clinical-trial evidence. For an early
clinical trial with no phase specified, use
`evidence_type = Early-phase clinical trial` and
`trial_phase = Unknown`.

## 4. Annotation principles

1.  `evidence_text` must be copied verbatim from the source. Use one
    exact sentence by default; multiple adjacent sentences are allowed
    when needed to establish the claim or its context.
2.  Do not paraphrase, normalize, or combine non-adjacent fragments into
    a fabricated sentence.
3.  Preserve numbers, units, confidence intervals, p-values, endpoint
    names, and uncertainty exactly as reported.
4.  Structured fields represent the annotator's interpretation of the
    source text; do not infer facts absent from the source.
5.  Distinguish association from causation. Do not infer causation from
    observational associations.
6.  Preserve specific outcomes, including PFS, OS, DFS, and RFS. Do not
    treat them as interchangeable or silently normalize endpoint names.
7.  The same biomarker may have different relationships in different
    treatment or population contexts.
8.  Create separate records for independent biomarker--outcome claims,
    different subgroups, or separable endpoint-specific findings. Keep
    combined biomarker or endpoint findings together only when the
    source reports them as one combined finding without
    independent/separable results.
9.  Record the specific population/subgroup supporting the claim, not
    automatically the entire study enrollment. Include subgroup sample
    size when reported.
10. Record `evidence_setting` separately from `evidence_type`; study
    design and experimental setting are not interchangeable.
11. Record `trial_phase` when applicable. Use `Unknown` when a clinical
    trial's phase is not reported and `N/A` when trial phase does not
    apply.
12. Record explicitly stated measurement methods in `annotation_notes`;
    do not infer a method from the biomarker name.
13. Use `annotation_notes` to document ambiguity, conflicting evidence,
    limitations, missing statistical details, evidence certainty, and
    interpretation decisions.

## 5. Fields deferred to future versions

The following are intentionally not part of schema v0.1:

-   `comparator`: a dedicated field for the treatment/comparator
    context.
-   `factor_type` (or equivalent): an explicit distinction between
    molecular biomarkers, clinical factors, treatment/exposure factors,
    and other factor types.
-   `measurement_method`: a dedicated field for assay or measurement
    method.
-   `source_cohort`: a dedicated field to distinguish cohorts within a
    publication, if needed.
-   Structured statistical fields such as effect estimate, confidence
    interval, p-value, unit, and reference group.
-   `evidence_certainty`: a dedicated field for GRADE or other
    evidence-certainty assessments.
-   `study_id`: an identifier in addition to PMID, if needed.
-   `source_section`: source location such as Methods, Results, or
    Conclusion.
-   Biomarker normalization to standard ontologies, detailed
    treatment-line/combination fields, automated confidence scores, and
    full-text paragraph-level provenance.

These fields may be reconsidered after the pilot annotation and
consistency review. Do not add them to v0.1 without an explicit version
change.

## 6. Record-level quality principles

Before accepting a record, confirm:

-   It represents one identifiable claim.
-   The biomarker/factor and relationship are supported by the source.
-   Direction is justified and, for predictive claims, tied to a named
    therapy and comparator.
-   The outcome endpoint and population are stated precisely.
-   `evidence_text` is exact and sufficient to support the
    interpretation.
-   Missing information is marked `Unknown` or `N/A`, not guessed.
-   Statistical limitations, uncertainty, and ambiguities are
    documented.
-   Another annotator could reproduce the interpretation from the
    evidence text and notes.

## 7. Version history

  -----------------------------------------------------------------------
  Version                             Description
  ----------------------------------- -----------------------------------
  0.1                                 Initial evidence schema for manual
                                      annotation pilot

  0.1 (updated)                       Clarified direction; expanded
                                      evidence types; added
                                      `evidence_setting` and
                                      `trial_phase`; aligned relationship
                                      vocabulary and annotation
                                      principles with Manual Evidence
                                      Annotation Guidelines v0.1

  0.1 (clarified)                     Enforced the evidence-setting
                                      controlled vocabulary; defined
                                      multi-setting storage and Response
                                      direction; documented the
                                      single-type limitation for mixed
                                      biomarker combinations
  -----------------------------------------------------------------------
