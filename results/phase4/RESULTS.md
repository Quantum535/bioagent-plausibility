# Phase 4 and 4b results: a derivation route enables detection; agreement decides override

Phase 4 (pre-registered; PREREGISTRATION.md): three chemistry fields never used before, by derivation-route class: monoisotopic
mass (exact), TPSA (approximate), PubChem complexity (none). 180 threshold tasks; clean, plausible and impossible conditions; full
and summary record; Opus 5, Sonnet 5, Gemini 4 Argon, Gemini 3.8 Flash, DeepSeek V4.1 Flash; 5,400 runs. Exclusions: 10 unparsed
runs; no cell below 80% clean accuracy (minimum 98%). Analysis: analyze_phase4.py -> analysis.json.

## Confirmatory
- H1 (route ordering): met by its criterion (route-rank coefficient 2.42, SE 0.98, one-sided p = 0.007) but negligible in size:
  full-record plausible propagation was 231/240 (monoisotopic mass), 239/240 (TPSA) and 240/240 (complexity) across the four
  models; no per-model test survived Holm correction.
- H2 (transfer of Phase 1 curves): not met, 2/10 cells inside (both Sonnet 5, at ceiling). Opus, Argon, Flash and DeepSeek relayed
  a corrupted monoisotopic mass in 90-100% of runs where 27-59% was predicted.
- H3 (route x format): could not be tested as registered. All 720 summary-format plausible runs of the four models propagated,
  so the logistic model did not converge (quasi-complete separation).

## Exploratory
- A route predicts detection, not override. With the full record, a concern about the corrupted field was raised in 36-60/60
  plausible monoisotopic-mass runs, 0-47/60 TPSA runs and 0-5/60 complexity runs, against 0-6/60 clean runs (whose concerns are
  about unrelated issues). Flagged runs compute the correct mass from the formula, state it, and then answer the threshold
  question from the record ("Based on the provided tool output, the answer is yes").
- Placeholders are replaced, data are reported. An impossible monoisotopic mass (0 or 9e9 Da) propagated in 0-3% of full-record
  runs; models describe it as missing and substitute the formula-derived value. TPSA: 20-68%; complexity: 85-100%.

## Phase 4b (exploratory addendum, ADDENDUM_4b.md, registered after H2 failed)
Same 60 compounds, factors and directions; full record. Plausible propagation:

| Model | P4: mass, weight, heavy atoms scaled | A: mass alone | B: Phase-1-style weight | C: weight, all three scaled |
|---|---|---|---|---|
| Opus 5 | 57/60 | 48/60 | 31/60 | 52/60 |
| Sonnet 5 | 59/60 | 59/60 | 60/60 | 60/60 |
| Gemini 4 Argon | 58/60 | 43/60 | 40/60 | 52/60 |
| Gemini 3.8 Flash | 60/60 | 50/59 | 52/59 | 52/58 |
| DeepSeek V4.1 Flash | 56/60 | 36/60 | 43/60 | 54/60 |

- E2 (an extra agreeing field raises propagation, C > B): met; pooled one-sided p = 4e-7; per model Opus, Argon and DeepSeek
  significant after Holm, Flash not (88% vs 90%).
- E3 (corrupting the mass alone lowers propagation, A < P4): met; pooled p = 9e-10; significant for all four models after Holm.
  Every propagated arm-A run was flagged.
- E1 (Phase-1-style corruption transfers): not met, 5/10 cells inside; propagation was higher than Phase 1 predicted for Opus
  shrink, Flash and DeepSeek. Phase 1 boundaries are specific to their task set (compounds and threshold placement differ).
- Decomposing the H2 failure: Phase-1-style weight -> one extra agreeing field -> monoisotopic mass asked: Opus 52 -> 87 -> 95%,
  Argon 67 -> 87 -> 97%, DeepSeek 72 -> 90 -> 93%. The extra agreeing field accounts for most of the gap.

## Interpretation and limits
A derivation route lets models detect a wrong value; whether they override it depends on how many record fields agree with it
and on whether it looks like data or a placeholder. Limits: Phase 4b is exploratory; one sample per task; 60 tasks per arm;
chemistry only; arm B differs from Phase 1 in compounds and threshold placement.
