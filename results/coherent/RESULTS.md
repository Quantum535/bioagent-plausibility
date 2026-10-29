# Phase 3 results: coherent corruption, a second source, and the harness all-clear

Models: Opus 5, Gemini 4 Argon, DeepSeek V4.1 Flash. Tasks: 50 shrink + 50 inflate protein length/mass tasks; 22 + 21 chemistry
weight/heavy-atom tasks. Coherent corruption edits the sequence (proteins) or swaps the structure (chemistry) and recomputes every
derived field, so derivation checks pass. P1-P3 were committed before any run (PREDICTIONS.md); addendum 1 (inflate v2) and
addendum 2 (summary no-harness control, P4) were committed after early runs and before the arms they describe.
Tables: make_phase3_table.py -> phase3_table.json (Wilson 95% CIs).

## Findings
1. Coherence defeats the full record (P1 supported). With the full record, coherent plausible corruptions propagated in 94-98% of
   protein-shrink runs, 70-96% of protein-inflate (v2) runs and 93-98% of chemistry runs, against 9% for Opus in the benchmark's
   full-record condition, where the record contradicted the value. The full record helps through internal contradiction.
2. Impossible but consistent (P2 mixed: 3 of 6 comparisons as predicted). Full-record propagation of a 3-residue protein: Opus 42%,
   Argon 12%, DeepSeek 24%; of a methane swap: 100%, 59%, 45%. In summary format the same coherent impossible proteins propagated
   in 94-100% of runs, against 32-44% for the benchmark's single-field impossible values. Caveat: the values differ (a 3-residue
   length is wrong for the named protein, not physically impossible like 0).
3. A visible artifact is a cue some models act on. At identical wrong lengths, an inflated sequence built from tandem repeats (v1)
   propagated less than one extended with a natural segment (v2) for Opus (40% vs 76%) and Argon (44% vs 70%). DeepSeek mentioned
   the repeat in 48/50 v1 runs and still propagated 92% (v2: 96%).
4. A second source works where it covers the entity (P3 partly supported). Covered entities: Argon 0% in every cell; Opus 0% except
   protein inflate (4/49); DeepSeek protein inflate 9/49, protein shrink plausible 3/50, chemistry 1/56. Uncovered entities
   propagated in 26/30 runs. Residuals concentrate where the record is longer than the second source (13/147 covered inflate runs vs
   3/300 shrink) and follow a flag-and-defer pattern: the agent reports both values and answers with the record ("1111 aa (record) /
   889 aa (AlphaFold)"). One DeepSeek run treated two lookups of the same database as independent confirmation.
5. A false all-clear does not raise propagation (P4 not supported). Proteins were at ceiling with or without the harness. In
   chemistry the all-clear arm propagated less than the no-harness summary arm (Opus impossible 86% -> 41%, plausible 100% -> 77%;
   DeepSeek plausible 93% -> 77%; Argon 86% -> 64% and 100% -> 95%). The early 16/16 that motivated P4 was a record-format effect.

## Methods notes
Three cache-key collisions were found and fixed. (a) The two second-source arms shared keys; both were rerun. (b) Phase 2 replace
runs had been served from annotate traces; rerun independently, annotate and replace agree (DeepSeek chemistry impossible/plausible
22%/24% vs 21%/22%; proteins <= 2%), so that Phase 2 claim stands on valid data. (c) Inflate v1 and v2 tasks shared keys; the
run-level leak check rejected every affected run, so no contaminated trace entered a results file. Affected files are kept under
_cache_contaminated/. The cache key now includes the harness mode, the second-source flag and a hash of the corruption payload.
