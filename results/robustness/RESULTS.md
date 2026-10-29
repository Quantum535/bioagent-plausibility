# Robustness results (ADDENDUM.md, registered before these runs)

## Part 1: enforcing the second source on real errors (replace mode, Phase 5 tasks, 3 samples)
- RR1 not supported: covered superseded propagation 10.7% (Opus, 25/234), 7.4% (Argon, 17/231), 2.6% (DeepSeek, 6/234).
- RR2 supported pooled (mean per model x task 0.081 replace vs 0.153 annotate; one-sided Wilcoxon p = 2.5e-4), but heterogeneous:
  DeepSeek fell from 31-36% (annotate, per sample) to 2.6%; Opus was unchanged (9% -> 11%); Argon rose (<= 1.3% -> 7.4%).
- In replace mode the record shows the second-source value and the superseded value appears only in the verification block, so
  every propagated run answered with the value the harness had removed (Opus 28/237, Argon 20/234, DeepSeek 9/237, including the
  uncovered protein). Trace check of the stated reasoning: pending.

## Part 2: repeatability (three samples)
- R1 holds in every sample (Opus 30/30 x3 on 30 tasks; Argon 87-92%; DeepSeek 97-100%); 90-100% of tasks unanimous.
- R2: Opus 9% and Argon <= 1.3% in every sample; DeepSeek 31-36% in every sample (the R2 failure is stable).
- R3: same direction in all samples (longer 21-25% vs shorter 11-13%); one-sided p = 0.007, 0.044, 0.116.
- E3 (A < P4) holds in all 12 model x sample cells; E2 (C > B) in 11 of 12 (Argon sample 1: equal).
- Pooled over three samples (B -> C -> P4): Opus 63 -> 91 -> 97%, DeepSeek 71 -> 84 -> 88%, Argon 72 -> 80 -> 96%,
  Flash 88 -> 91 -> 99%. A (mass alone) vs P4: Opus 77 vs 97%, Argon 72 vs 96%, Flash 85 vs 99%, DeepSeek 56 vs 88%.
  The extra agreeing field accounts for most of the Phase-1-to-Phase-4 gap for Opus and DeepSeek; for Argon the field asked matters more.
- Mid-range cells are stochastic per task (20-46/60 tasks unanimous in arms A-C) while rates are stable; all tests treat tasks as units.

## Trace check of Part 1 (replace) residuals
Two mechanisms, at least: (1) Argon read the verification block's "observed" field (the original database value) as the
second-source measurement and answered with it ("verification against the AlphaFold DB sequence ... gives an observed length of
1116"); the block reused annotate's field names, which are ambiguous after replacement (a presentation flaw in our harness).
(2) Opus cited a recalled "canonical UniProt" length that matches the superseded version ("The canonical UniProt entry for
O60294 is 696 residues"), i.e. parametric memory of an earlier database state. Part 3 tests presentation directly.
