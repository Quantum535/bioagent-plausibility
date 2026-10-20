#!/usr/bin/env python3
"""Propagation by corruption direction (shrink vs inflate) for length/mass tasks in a task set."""
import argparse, glob, json
from pathlib import Path
from grade import aggregate, fmt, load_runs, model_label, score, sort_models

ap = argparse.ArgumentParser()
ap.add_argument("--traces", nargs="+", default=["results/v2/traces*.jsonl"])
ap.add_argument("--tasks", default="data/tasks_v2.json")
ap.add_argument("--out", default="results/v2/by_direction.md")
args = ap.parse_args()

direction = {t["task_id"]: t.get("direction") for t in json.load(open(args.tasks))["tasks"]}
rows = [score(r) for r in load_runs(args.traces)]
for r in rows:
    r["direction"] = direction.get(r["task_id"])
rows = [r for r in rows if r["direction"] in ("shrink", "inflate")]
models = sort_models({r["model"] for r in rows})

L = ["# Propagation by corruption direction (length and mass tasks only)\n",
     "Cells: propagation rate [Wilson 95% CI] (k/n). Shrink = corrupted value below truth; inflate = above.\n",
     "| model | condition | shrink | inflate | flagged (shrink) | flagged (inflate) |", "|---|---|---|---|---|---|"]
print(f"{'model':22s} {'condition':20s} {'shrink':>10s} {'inflate':>10s}")
for m in models:
    for cond in ("impossible", "plausible", "impossible+verify", "plausible+verify"):
        cells = {}
        for d in ("shrink", "inflate"):
            sub = [r for r in rows if r["model"] == m and r["condition"] == cond and r["direction"] == d]
            cells[d] = aggregate(sub) if sub else None
        if not cells["shrink"] or not cells["inflate"]:
            continue
        s, i = cells["shrink"], cells["inflate"]
        L.append(f"| {model_label(m)} | {cond} | {fmt(s['propagation'])} | {fmt(i['propagation'])} | "
                 f"{fmt(s['flag_rate'])} | {fmt(i['flag_rate'])} |")
        ps = fmt(s["propagation"]).split(" ")[0]; pi = fmt(i["propagation"]).split(" ")[0]
        print(f"{model_label(m):22s} {cond:20s} {ps:>10s} {pi:>10s}")
Path(args.out).write_text("\n".join(L) + "\n")
print(f"wrote {args.out}")
