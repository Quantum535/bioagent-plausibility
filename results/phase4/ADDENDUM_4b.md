# Phase 4b addendum (exploratory), written 2026-10-28 after the Phase 4 confirmatory analysis and before any 4b run

Why it was added: H2 failed. With the formula and SMILES in the record, four models relayed a +-20% monoisotopic-mass corruption in
90-100% of runs (Phase 1 molecular-weight curves predicted 27-59%), although most of those runs flagged the value and computed the
correct mass from the formula in their answer. Phase 4 differed from Phase 1 in three ways: the field asked (monoisotopic mass vs
molecular weight), the number of record fields agreeing with the corrupted value (three vs two), and the compounds.

Design: the 60 Phase 4 monoisotopic-mass compounds, with the same factors and directions; full record; Opus 5, Sonnet 5,
Gemini 4 Argon, Gemini 3.8 Flash, DeepSeek V4.1 Flash; one sample per task x condition x model.
- A: monoisotopic mass corrupted alone (molecular weight and heavy-atom count clean); monoisotopic-mass question; Phase 4 record format.
- B: Phase-1-style corruption (molecular weight and heavy-atom count scaled together); molecular-weight question; original record
  format (no monoisotopic mass, TPSA or complexity fields).
- C: Phase 4 corruption (monoisotopic mass, molecular weight and heavy-atom count scaled together); molecular-weight question;
  Phase 4 record format.

Exploratory expectations (reported whatever the outcome):
- E1 (transfer): arm B falls inside the H2 prediction intervals in at least 8 of 10 model x direction cells.
- E2 (an extra agreeing field): propagation is higher in C than in B.
- E3 (agreement among record fields): propagation is lower in A than in Phase 4 monoisotopic mass.
- The field asked (C vs Phase 4 monoisotopic mass) is reported descriptively.
Analysis: E2 and E3 by logistic regression prop ~ arm + model + direction (one-sided, alpha 0.05) on Opus 5, Argon, Flash and
DeepSeek, with per-model Fisher tests (Holm) as secondary. Exclusions as in Phase 4. If a regression cannot be fitted because a
cell is at 0% or 100%, the per-model Fisher tests are reported instead and the failure is stated.
