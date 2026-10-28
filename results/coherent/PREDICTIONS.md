# Phase 3 predictions, written before any model output was read (2026-10-28)
P1. Coherent-plausible, full record, no harness: propagation returns to summary-plausible levels (>=70% all three models),
    vs 1-9% for contradictory full-record plausible. The full record helps only through its internal contradiction.
P2. Coherent-impossible (3-residue protein / methane), full record: propagation falls below the summary-impossible baseline
    (rule and recall cues still apply) but stays above 0; no crossfield cue is available.
P3. Harness annotate with the second-source block: propagation <=5% on covered entities for both conditions;
    uncovered entities behave as P1/P2.

## Addendum (2026-10-28 ~09:20 PT): written after reading Opus 5 v1 inflate results, before any v2 run
v1 coherent inflate lengthened sequences with tandem copies of the C-terminal 60 residues. Opus 5 propagated 20/50
(vs 49/50 for shrink); repeat-related wording appeared in 50/50 coherent inflate traces vs 2/50 clean.
v2 (data/coherent_inflate_v2.json) reaches the same target lengths with a natural segment from a different benchmark
protein, sharing no 12-mer with the target. P1 is evaluated on v2; v1 is reported as a cue ablation (same wrong length,
visible repeat vs none). The harness arm uses v2.
