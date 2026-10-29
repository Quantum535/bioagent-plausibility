# Phase 5 results: real, historically corrected UniProt errors

Design (pre-registered, PREREGISTRATION.md): 79 benchmark proteins whose sequence UniProt later revised with a length change. The
superseded condition shows the most recent such superseded sequence with its own length and mass (current annotations trimmed to
the old length; UniSave provides historical sequences, not historical entries). Arms: full record; summary record; summary record
with harness annotation including AlphaFold DB as a second source. Models: Opus 5, Gemini 4 Argon, DeepSeek V4.1 Flash. No
exclusions; clean accuracy 100% in every cell (Opus full-record clean on 20 tasks). DeepSeek's first run failed entirely at the API
(a network-level block); failed runs are not cached and all were rerun.

## Confirmatory
- R1 supported (6/6 cells >= 80%): without a second source, superseded values were relayed in 90-100% of runs (full record /
  summary: Opus 99% / 100%, Argon 90% / 100%, DeepSeek 99% / 100%).
- R2 not supported: with AlphaFold DB as second source, propagation on covered proteins was 9.0% (Opus, 7/78), 1.3% (Argon, 1/78)
  and 30.8% (DeepSeek, 24/78). DeepSeek flagged the discrepancy in 24 of its 25 propagated runs.
- R3 supported: residual propagation with the second source was higher when the superseded record was longer than the current one:
  16/63 (25%) vs 19/174 (11%), one-sided Fisher p = 0.007 (covered only: 16/63 vs 16/171, p = 0.002).

## Exploratory
- No size gradient: revisions changing the length by more than 50 residues were relayed in 47/48 full-record runs and 48/48 summary
  runs, against 78/81 and 81/81 for 1-5 residue revisions.
- The protein without AlphaFold coverage (r014) was relayed in all 9 model x arm cells.
- Full-record flag rates are not interpreted: superseded sequences sit under current annotations, which may disagree with them, so
  flags in the full record may reflect the construction rather than the error.
- Against Phase 3: second-source residuals are similar for Opus (8% on inflate in Phase 3, 9% here) and Argon (about 0%); DeepSeek
  is higher on real errors (31% vs 18%).

## Limits
One sample per task; 79 proteins; historical annotations unavailable; the second source carries the current sequence; Opus
full-record clean condition on 20 tasks only.
