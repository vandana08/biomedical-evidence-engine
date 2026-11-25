# Gold-Standard Annotation Consistency Review

**Dataset:** `pilot_annotations_source_verified_v10(1).csv`  
**Review basis:** Manual Annotation Guideline v0.1 (full-abstract clarification) and Evidence Schema v0.1 (clarified)  
**Scope:** 17 records (EV001–EV017), 6 PMIDs, 16 fields  
**Review outcome:** Approved as the pilot gold-standard CSV, with the scope and provenance notes below.

## 1. Structural validation

| Check | Result |
|---|---|
| Records | 17 |
| Fields | 16; matches Evidence Schema v0.1 |
| Evidence IDs | EV001–EV017; unique and sequential |
| PMID values | All populated and formatted as numeric PMIDs |
| Blank cells | 0 |
| Exact duplicate rows | 0 |
| Controlled-vocabulary violations | 0 |

All checked controlled-vocabulary values are valid for `biomarker_type`, `relationship`, `direction`, `evidence_type`, `evidence_setting`, and `trial_phase`.

## 2. Annotation consistency review

| Area | Result | Review note |
|---|---|---|
| Unit of annotation | Pass | Records represent identifiable biomarker–relationship–outcome claims, with subgroup and endpoint splits where appropriate. |
| Biomarker and type | Pass with documented ambiguity | EV001–EV002 retain the source-reported EGFR C797S/T790M combination and explicitly note that the abstract does not establish whether the mutations were studied jointly or separately. EV003 appropriately uses `Unknown` at the individual-responder level. |
| Relationship | Pass | The records distinguish Response, Prognostic, Predictive, Resistance, and Association in line with the operational definitions. Single-treatment-group findings are not labeled Predictive. |
| Direction | Pass | Favorable responses are Positive; unfavorable outcomes are Negative; explicit non-significant findings are Neutral; non-significant trends or insufficiently directional findings are Unclear. |
| Outcomes | Pass | Distinct endpoints are retained separately where results are separable, including EV007, EV016, and EV017. |
| Evidence type / setting / phase | Pass | Values conform to the v0.1 controlled vocabularies. Non-trial records use `N/A` for trial phase. |
| Population and treatment context | Pass with notes | Subgroups and sample sizes are included where reported; unknown individual mutation status is not inferred. |
| Evidence text | Pass | Text is verbatim and includes adjacent context where needed, notably EV002 and EV004. Endpoint-specific records retain the complete source sentence where multiple endpoint results appear in that sentence. |
| Annotation notes | Pass | Relevant uncertainty, limitations, and interpretation choices are documented. |

## 3. Full-abstract scope clarification

The updated guideline makes the complete abstract in scope: Introduction/Background, Methods, Results, and Conclusion. This is compatible with the current 16-field schema.

The CSV does not have a dedicated `source_section` field, which remains deferred. Therefore, this review can check the supplied evidence text and annotation notes, but cannot independently identify which abstract section contributed every structured field. This is a known v0.1 provenance limitation, not a structural defect.

The evidence text should remain the minimum verbatim text sufficient to support each claim; using the full abstract as the annotation source does not mean copying the entire abstract into every record.

## 4. Scope note: EV014–EV015

EV014 and EV015 concern hs-cTnT / NT-proBNP and cognitive impairment in chronic heart failure. Their notes identify them as out-of-domain for an EGFR–NSCLC-specific corpus.

- If the pilot is intended to evaluate a **general biomedical evidence extraction system**, retain them as valid cross-domain examples.
- If the pilot is intended to evaluate an **EGFR–NSCLC-only system**, treat them as explicit out-of-domain challenge/negative examples and exclude them from the in-domain performance denominator.

Do not delete or relabel these records without making that evaluation-scope decision explicit.

## 5. Record-level review notes

- **EV001–EV002:** The combined mutation wording is retained with the uncertainty documented. EV002 includes the adjacent sentence that establishes the model context for the xenograft finding.
- **EV003:** Individual responders' mutation status is not reported; `biomarker = Unknown` avoids assigning a genotype to the three responders.
- **EV004:** Non-significant mutation-subtype trends are recorded as Association / Unclear rather than as an established prognostic effect.
- **EV005–EV006:** RFS and OS findings remain separate, with their distinct reported directions.
- **EV007, EV016, EV017:** ORR, DCR, and PFS are separate records. The source sentence is repeated because it reports all three endpoint-specific results together.
- **EV008–EV011:** Detection of C797S, T790M loss, competing resistance mechanisms, and the serial plasma-level association are not conflated into one claim.
- **EV012–EV013:** Mutation-positive and mutation-negative subgroups retain separate predictive directions relative to gefitinib.
- **EV014–EV015:** The statistical uncertainty and very low GRADE certainty are retained in notes.

## 6. Final disposition

**Approved as the supplied 17-record pilot gold-standard CSV for v0.1.**

No changes have been made to the CSV. The review found no structural or controlled-vocabulary errors requiring correction. Preserve this exact file as the reviewed gold-standard version and retain this audit alongside it.

Before reporting model performance, explicitly define whether EV014–EV015 are in-domain or out-of-domain for the target corpus.
