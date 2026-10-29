# Robustness addendum (Phases 4b and 5), written 2026-10-29 before any of these runs

## Part 1: enforcing the second source on real errors (Phase 5 tasks)
Arm: summary record with the harness in replace mode plus the AlphaFold DB second source: where the second source disagrees, the
record shows the second-source value, and the verification block still lists the original value. Models: Opus 5, Gemini 4 Argon,
DeepSeek V4.1 Flash; clean (1 sample) and superseded (3 samples) on all 79 tasks.
- RR1: on covered proteins, superseded propagation is at most 2% for each model (pooled over samples).
- RR2: replace propagates less than annotate (Phase 5 arm 3, now with 3 samples): per model x task mean propagation over samples,
  one-sided Wilcoxon signed-rank test, pooled across models, alpha = 0.05.
- Reported descriptively: runs in which the agent answers with the original value shown in the verification block.

## Part 2: repeatability (descriptive robustness checks, no new hypotheses)
Two further samples (three in total; sample 0 is the original run) for: Phase 5 full-record superseded (Opus on the first 30
tasks, Argon and DeepSeek on all 79); Phase 5 annotate + second source (all three models); Phase 4b arms P4, A, B and C
(Opus 5, Argon, Flash, DeepSeek). For each cell we report propagation per sample and the share of tasks with the same outcome in
all three samples, and we check whether each original conclusion holds in every sample separately: R1 (>= 80%), R2 and R3
(Phase 5), and the signs of E2 (C > B) and E3 (A < P4) for each model.
