"""Phase 5 pre-registration, with counts computed from the task file. Writes results/phase5/PREREGISTRATION.md."""
import json, datetime
import domains
from harness.second_source import check_protein_ss
dom = domains.load("protein"); Ts = dom.Table("data/proteins_v2.json")
T = json.load(open("data/phase5_tasks.json"))["tasks"]; old = json.load(open("data/unisave_old_sequences.json"))
n_out = sum(any(x["same_as_stored"] for x in v) for v in old.values())
d = [abs(t["corruptions"]["superseded"]["d_length"]) for t in T]; n = len(T)
nl = sum(t["target_field"] == "length" for t in T); nlong = sum(t["direction"] == "old_longer" for t in T)
ss = sum(check_protein_ss(t["target_accession"], json.loads(dom.render(Ts, Ts.by_acc[t["target_accession"]], t["corruptions"]["superseded"])))[t["target_field"]]["status"] == "mismatch" for t in T)
doc = f"""# Phase 5 pre-registration: do real, historically corrected UniProt sequence errors propagate?

Written {datetime.date.today()} before any Phase 5 model run (mock runs only).

## Data
UniSave sequence history for the 300 benchmark proteins (fetch_unisave.py, fetch_unisave_sequences.py): 167 proteins have at
least two sequence versions (257 superseded sequences). {n_out} proteins whose stored record has itself been superseded since the
benchmark was built are excluded. For each remaining protein whose sequence was revised with a length change, the most recent such
superseded sequence defines one task (make_phase5_tasks.py): {n} tasks; {nl} length and {n - nl} mass threshold questions; superseded
record longer than the current one in {nlong}, shorter in {n - nlong}; |length change| 1-5 residues: {sum(x <= 5 for x in d)},
6-50: {sum(5 < x <= 50 for x in d)}, >50: {sum(x > 50 for x in d)}. The threshold lies between the current and the superseded value.

## Design
Conditions: clean (current entry) and superseded (the record shows the old sequence with its own length and mass; other
annotations are current, with features beyond the old length removed, because UniSave provides historical sequences rather than
historical JSON entries). Derivation checks pass on every superseded record; AlphaFold DB (current sequence) disagrees with the
target field on {ss}/{n}.
Arms: (1) full record, no harness; (2) summary record, no harness; (3) summary record with harness annotation including the
second source (AlphaFold DB). Models: Opus 5, Gemini 4 Argon, DeepSeek V4.1 Flash; one sample per task x condition x arm x model.
For cost, Opus runs the full-record clean condition on the first 20 tasks only.
Outcome: propagated = the parsed answer equals the answer implied by the superseded record.

## Predictions (from Phase 3 coherent corruptions)
R1. Without a second source (arms 1 and 2), superseded values propagate in at least 80% of superseded runs in at least 5 of the
6 model x arm cells.
R2. With the second source (arm 3), propagation among superseded runs on proteins it covers is at most 10% for each model.
R3. With the second source, residual propagation is higher when the superseded record is longer than the current one than when it
is shorter (pooled across models; one-sided Fisher exact test, alpha = 0.05).

## Exclusions
API errors; unparsed answers; model x arm cells with clean accuracy below 80% are excluded from R1-R3.

## Exploratory, not tested
Propagation by size of the historical change; flagged-yet-propagated rates; behaviour on the uncovered protein.
"""
open("results/phase5/PREREGISTRATION.md", "w").write(doc); print(doc)
