# Cue-taxonomy validation and relabelling (2026-10-30)

## Human labels
Two annotators labelled 300 concerns (200 protein, 100 chemistry; sampled from the v2 protein and chemistry traces by
make_validation_set.py) blind, with GUIDELINES.md and label_tool.py. Inter-annotator agreement before adjudication (Cohen's kappa):
protein cross-field 0.73, recall 0.84, rule 0.83, none 0.66 (2 and 1 positives); chemistry 0.86, 0.89, 0.74, 0.81.
Disagreements were resolved jointly into consensus labels (adjudicate.py).

## The original regex grader
Against the consensus: protein cross-field 0.48, recall 0.08, rule 0.40, none 0.05; chemistry 0.41, 0.68, 0.44, 0.47.
It undercounted protein recall by about 30 points and labelled many cited reasons "none". It was replaced.

## Replacement classifier
An LLM given the annotator guidelines (cue_prompt.txt), 10 concerns per request. Developed on a frozen half of the consensus set
(seed 30; 100 protein, 50 chemistry) over three rounds logged in GUIDELINES.md; Haiku 4.5 and Sonnet 5 were compared in the final
round under a pre-stated rule (Sonnet 5 cleared 0.6 in 6/6 cells, Haiku in 2/6). Frozen at commit 295f711 before a single run on
the held-out half. Test kappa: protein cross-field 0.81, recall 0.81, rule 0.65 (5 positives), none 1.00 (1 positive); chemistry
0.87, 0.75, 0.68, 0.56. The pre-stated criterion (>= 0.6 for cross-field, recall and rule in both domains) was met.

## Relabelling
All 13,021 concerns used by the paper's figures (v2 protein, chemistry, boundary sweep, full-record) were relabelled through the
Message Batches API with requests identical to the validated calls (280 concerns via single-request fallback; about $25).
The figure pipeline reads them through validated_cues.py; all 15,415 cue lookups matched a validated label (no regex fallback).

## What changed (share of flagged runs citing each cue, old regex -> validated)
| Group (flagged runs) | cross-field | recall | rule | none | relayed if cross-field / recall / rule |
|---|---|---|---|---|---|
| protein impossible (1,894) | 63 -> 81 | 48 -> 59 | 18 -> 16 | 17 -> 0 | 70/71/36 -> 67/70/29 |
| protein plausible (783) | 49 -> 67 | 48 -> 89 | 0 -> 0 | 20 -> 1 | 46/95/- -> 44/64/(too few) |
| sweep, consistent (843) | 5 -> 6 | 62 -> 88 | 3 -> 3 | 35 -> 7 | 100/99/100 -> 100/99/96 |
| sweep, inconsistent (944) | 86 -> 91 | 60 -> 41 | 7 -> 1 | 7 -> 3 | 86/84/73 -> 85/83/78 |
| chemistry impossible (855) | 32 -> 44 | 64 -> 59 | 47 -> 38 | 13 -> 4 | 58/51/58 -> 60/48/59 |
| chemistry plausible (547) | 17 -> 24 | 84 -> 92 | 6 -> 1 | 12 -> 2 | 99/97/94 -> 96/97/(too few) |

Claims after validation: (1) flags almost always cite a specific reason (none <= 7% in every group); (2) cross-field cues track
record inconsistency (6% vs 91% in the sweep), and memory drives 88% of flags when the record is consistent; (3) rule-cued protein
flags relay the wrong value far less often (29%) than cross-field or recall-cued ones (67-70%); chemistry shows no such advantage;
(4) recall-cued plausible protein flags relay 64% of the time (previously reported 95%).
