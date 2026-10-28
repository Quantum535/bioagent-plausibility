# Phase 4 pre-registration: does a field's derivation route predict whether agents relay a corrupted value?

Written 2026-10-28 before any Phase 4 model outcome was inspected. A 36-run cost-only pilot (6 tasks, clean and
plausible, full record, Opus 5 / Argon / DeepSeek) was run to price the study; only its cost line was read. Those runs are
cached and form part of the sample.

## Background
In the benchmark, corrupted values were corrected only when the record offered a derivation route (sequence to length and mass,
formula to weight). Phase 4 tests that claim out of sample on three chemistry fields never used before, whose route class was
fixed from data before any model run (fetch_phase4_fields.py, commit dd7e537):
- Monoisotopic mass, exact route: RDKit reproduces PubChem from the record's formula/SMILES for 300/300 compounds (within 0.001 Da).
- TPSA, approximate route: RDKit (S and P included) within 0.1 square angstroms for 80% of compounds, Spearman 0.996.
- PubChem complexity, no route: the closest RDKit analogue (Bertz CT) agrees for 1.7% of compounds; rank correlation only (0.936).

## Design
180 threshold questions ("Does the compound with PubChem CID X have a [field] greater than T?"), 30 per field x direction,
one distinct compound per task (data/chem/phase4_tasks.json; make_phase4_tasks.py, seed 4). T lies midway between the true
and the plausibly corrupted value, so a relayed corruption flips the answer.
Conditions: clean; plausible (value x factor; shrink [0.75, 0.8], inflate [1.2, 1.25]); impossible (0 or negative, or absurdly large).
Monoisotopic mass is corrupted together with molecular weight and heavy-atom count, so the formula and SMILES are the only
contradiction, as in the Phase 1 boundary experiment.
Formats: full record (formula and SMILES present, the route) and summary record (neither present, no route for any field).
Models: Opus 5, Sonnet 5, Gemini 4 Argon, Gemini 3.8 Flash, DeepSeek V4.1 Flash. One sample per task x condition x format x
model (5,400 runs). Outcome: propagated = the parsed answer equals the answer implied by the corrupted record.

## Hypotheses
H1 (route ordering). In full-record plausible runs, propagation increases with route class: monoisotopic mass < TPSA < complexity.
Primary test: logistic regression, propagated ~ route rank (0, 1, 2) + model + direction, on full-record plausible runs of
Opus 5, Argon, Flash and DeepSeek; one-sided Wald test that the route-rank coefficient is > 0, alpha = 0.05. Sonnet 5 is
excluded from H1 in advance: its Phase 1 chemistry curve predicts ceiling propagation even for the exact-route field (H2),
leaving no room for an ordering. Secondary: per-model one-sided Fisher exact tests (mono < TPSA; TPSA < complexity),
Holm-corrected across the 8 tests.

H2 (quantitative transfer). Monoisotopic-mass propagation in full-record plausible runs falls inside the prediction interval
derived from each model's Phase 1 chemistry molecular-weight curve at the factors used here (log-linear interpolation; the
interval combines binomial error from n = 30 new tasks and n = 40 Phase 1 tasks per point). Supported if at least 8 of the
10 model x direction cells fall inside their interval.

H3 (the route is what matters). The route-rank effect is larger with the full record than with the summary record: in a
logistic regression on plausible runs of both formats (same four models), the route rank x full-format interaction is
positive (one-sided, alpha = 0.05).

## Predictions for monoisotopic mass (H2)
| Model | Direction | Predicted propagation | 95% prediction interval |
|---|---|---|---|
| Opus 5 | shrink | 31% | [9%, 53%] |
| Opus 5 | inflate | 29% | [7%, 50%] |
| Gemini 4 Argon | shrink | 59% | [35%, 82%] |
| Gemini 4 Argon | inflate | 49% | [26%, 73%] |
| Gemini 3.8 Flash | shrink | 50% | [27%, 74%] |
| Gemini 3.8 Flash | inflate | 52% | [28%, 76%] |
| DeepSeek V4.1 Flash | shrink | 27% | [6%, 48%] |
| DeepSeek V4.1 Flash | inflate | 58% | [35%, 82%] |
| Sonnet 5 | shrink | 95% | [85%, 100%] |
| Sonnet 5 | inflate | 100% | [93%, 100%] |

Also expected, not formally tested: complexity propagates at summary-plausible levels (90% or more) in both formats, and TPSA
falls between the other two fields.

## Exclusions
Runs that fail at the API are retried until they succeed; persistent failures are excluded and counted. Runs with no
parseable answer are excluded from propagation rates and reported per cell. If clean accuracy for any model x field x format
is below 80%, that cell is reported as a task problem and excluded from H1 to H3.

## Exploratory, not tested
The impossible condition; flagged-yet-propagated rates; shrink vs inflate asymmetry; comparison with Phase 3 coherent corruption.
