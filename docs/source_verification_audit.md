# Pilot Evidence Source-Verification Audit

**Dataset reviewed:** `pilot_annotations_gold_standard_reviewed.csv`\
**Updated dataset:** `pilot_annotations_source_verified_v10.csv`\
**Scope:** 17 records across six PubMed identifiers\
**Schema:** Evidence Schema v0.1\
**Guideline:** Manual Evidence Annotation Guideline v0.1

## 1. Verification approach

Each evidence record was compared with the abstract for its cited PMID.
Where a field depended on trial details or interpretation beyond the
abstract, the relevant trial registry or available full text was
checked. This audit verifies source alignment and annotation
consistency; it does not independently reproduce the underlying
statistical analyses.

## 2. Overall result

All six cited PMIDs were located and their records/abstracts reviewed.
The reported source sentences, study identifiers, subgroup counts,
endpoints, and numerical results were supported, subject to the
corrections below.

  ------------------------------------------------------------------------------
  PMID              Publication / source     Records           Verification
  ----------------- ------------------------ ----------------- -----------------
  41649868          JIN-A02 in EGFR          EV001--EV003      Abstract
                    C797S/T790M NSCLC                          sentences
                                                               verified; Phase
                                                               I/II trial
                                                               context checked
                                                               against NCI trial
                                                               information

  40803053          Real-world first-line    EV004             Abstract sentence
                    afatinib cohort in                         and PFS context
                    Indonesia                                  verified

  39569608          PD-L1 expression in      EV005--EV007,     Abstract wording,
                    resected EGFR-mutant     EV016--EV017      subgroups,
                    lung adenocarcinoma                        endpoints and
                                                               p-values verified

  30073261          Acquired resistance to   EV008--EV011      Abstract wording,
                    osimertinib                                cohort sizes,
                                                               validation cohort
                                                               and serial plasma
                                                               finding verified

  19692680          Gefitinib versus         EV012--EV013      Complete subgroup
                    carboplatin-paclitaxel                     sentence, sample
                    (IPASS)                                    sizes and hazard
                                                               ratios verified

  42865942          Biomarkers and cognitive EV014--EV015      Abstract
                    impairment in chronic                      statistics and
                    heart failure                              GRADE statement
                                                               verified;
                                                               full-text weight
                                                               contribution
                                                               checked
  ------------------------------------------------------------------------------

## 3. Corrections made

### EV001--EV003: Response direction

All three records describe favorable treatment-response findings: -
EV001: antiproliferative activity in preclinical models. - EV002: tumor
regression in xenograft models. - EV003: three partial responses in
early clinical data.

Under the guideline's Response direction rule, their `direction` is now
`Positive`, rather than `Unclear`. This describes the reported response,
not a claim that the biomarker independently predicts benefit or that
the drug is superior to a comparator.

### EV002: preserve biomarker context in evidence text

The xenograft sentence does not itself name EGFR C797S/T790M. The
immediately preceding sentence establishes that JIN-A02 was evaluated in
models harboring these mutations. Both adjacent sentences are now
included verbatim in `evidence_text` to support the record's biomarker
context.

### EV004: preserve PFS context

The sentence about mutation-subtype trends does not repeat the endpoint.
The immediately preceding Results sentence identifies PFS as the outcome
under discussion. Both adjacent sentences are now included verbatim so
that the PFS context is explicit.

### EV009: clarify validation design

The primary time-to-treatment-discontinuation result comes from the
41-patient post-resistance tumor-NGS cohort. The abstract separately
reports confirmation in a 110-patient validation cohort using plasma
cell-free DNA genotyping. The annotation note now distinguishes the
primary observational evidence from the validation cohort.

## 4. Record-level source checks

  -----------------------------------------------------------------------
  Records                             Source-level result
  ----------------------------------- -----------------------------------
  EV001                               Antiproliferative finding and
                                      C797S/T790M model context match the
                                      abstract

  EV002                               Tumor-regression sentence matches;
                                      adjacent preceding sentence added
                                      to establish mutation context

  EV003                               Partial-response sentence matches;
                                      Phase I/II classification is
                                      supported by the linked JIN-A02
                                      trial information; individual
                                      responder mutation status remains
                                      unspecified

  EV004                               Mutation-subtype trend sentence
                                      matches; adjacent PFS context added

  EV005                               RFS association sentence and
                                      p-value match

  EV006                               OS non-association sentence and
                                      p-value match

  EV007, EV016, EV017                 The same source sentence reports
                                      ORR, DCR and PFS with separate
                                      p-values; separate endpoint records
                                      are justified

  EV008                               Maintained-T790M subgroup count and
                                      C797S count match

  EV009                               T790M-loss
                                      treatment-discontinuation
                                      comparison and 110-patient
                                      validation statement match

  EV010                               T790M-loss subgroup count and
                                      examples of competing resistance
                                      mechanisms match

  EV011                               Serial plasma mutant-EGFR finding,
                                      timing, percentages and p-value
                                      match

  EV012, EV013                        Complete subgroup sentence, 261/176
                                      subgroup sizes, HRs, CIs and
                                      p-values match; the two records
                                      represent distinct biomarker
                                      subgroups

  EV014                               hs-cTnT mean difference, CI,
                                      p-value and I² match; full text
                                      confirms 95.8% of pooled weight
                                      came from one study and GRADE
                                      certainty was very low

  EV015                               NT-proBNP mean difference, CI,
                                      p-value and I² match; GRADE
                                      certainty was very low
  -----------------------------------------------------------------------

## 5. Interpretation checks retained

-   EV001--EV003 are Response records. Positive direction refers to the
    favorable response reported in the specified model or patient
    context; it does not establish a biomarker-by-treatment interaction.
-   EV003 does not identify the specific EGFR mutation carried by each
    responder.
-   EV004 remains Association with Unclear direction. The abstract
    reports non-significant mutation-subtype trends and calls for
    broader multicenter validation; it does not establish a prognostic
    subtype effect.
-   EV007/EV016/EV017 remain Association, not Predictive, because they
    describe findings within a single post-relapse EGFR-TKI-treated
    subgroup and do not establish differential treatment benefit.
-   EV008 records C797S detection in the maintained-T790M resistance
    subgroup; no independent C797S outcome effect is reported.
-   EV009 records the unfavorable association between T790M loss and
    shorter time to treatment discontinuation.
-   EV010 does not establish individual clinical effects for each
    competing mechanism listed.
-   EV011 records the association between T790M loss and serial plasma
    EGFR driver-mutation change; it does not establish a clinically
    validated monitoring test.
-   EV014 is statistically significant but has very low GRADE certainty
    and is heavily weighted toward one study.
-   EV015 is non-significant, with a confidence interval crossing zero;
    direction remains Unclear.

## 6. Final structural validation

-   17 records; 17 unique evidence IDs (EV001--EV017).
-   16 schema fields retained in the expected order.
-   No blank cells.
-   PMID identifiers retained as strings.
-   Controlled-vocabulary values remain valid.
-   Non-clinical-trial records use `trial_phase = N/A`.
-   EV003 remains Phase I/II; EV012 and EV013 remain Phase III.

## 7. Conclusion

The updated CSV is suitable to be treated as the **source-verified pilot
annotation set for the evidence statements reviewed here**. It is still
a small pilot gold standard, not a statistically representative
benchmark. Preserve the schema and guideline versions used for
annotation, and avoid changing these records silently after the freeze;
any subsequent adjudication should be versioned and documented.
