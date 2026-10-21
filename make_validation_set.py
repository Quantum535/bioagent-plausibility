#!/usr/bin/env python3
"""Sample flagged concerns for human cue labelling -> results/v2/validation/concerns_to_label.csv (blind)
and concerns_key.json (model/condition/classifier labels, kept separate from the labelling sheet)."""
import argparse, csv, json, random
from pathlib import Path
from analysis import classify, CHEM_FIELDS
from grade import load_runs, score

ap = argparse.ArgumentParser()
ap.add_argument("--traces", nargs="+", default=["results/v2/traces*.jsonl"])
ap.add_argument("--n", type=int, default=200)
ap.add_argument("--seed", type=int, default=41)
ap.add_argument("--out_dir", default="results/v2/validation")
args = ap.parse_args()
out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

rows = [score(r) for r in load_runs(args.traces)]
flagged = [r for r in rows if r["flagged"] and r["concerns"] and r["base_condition"] != "clean"]
rng = random.Random(args.seed)
# stratify: equal share per (model, condition) cell, then fill to n at random
cells = {}
for r in flagged:
    cells.setdefault((r["model"], r["condition"]), []).append(r)
per_cell = max(1, args.n // len(cells))
sample = []
for k in sorted(cells):
    rng.shuffle(cells[k]); sample += cells[k][:per_cell]
rest = [r for k in cells for r in cells[k][per_cell:]]
rng.shuffle(rest); sample += rest[:max(0, args.n - len(sample))]
rng.shuffle(sample)

with open(out / "concerns_to_label.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "concern_text", "cross_field", "recall", "rule", "unspecific", "notes"])
    for i, r in enumerate(sample):
        w.writerow([f"c{i:03d}", " || ".join(r["concerns"]), "", "", "", "", ""])
key = [{"id": f"c{i:03d}", "model": r["model"], "condition": r["condition"], "task_id": r["task_id"],
        "target_field": r["target_field"], "classifier": classify(r["concerns"], chem=r["target_field"] in CHEM_FIELDS)} for i, r in enumerate(sample)]
(out / "concerns_key.json").write_text(json.dumps(key, indent=1))
print(f"wrote {len(sample)} concerns to {out}/concerns_to_label.csv (blind) and concerns_key.json")
print("Label each row with 1/0 in cross_field, recall, rule; unspecific=1 only if the other three are all 0.")
