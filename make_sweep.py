#!/usr/bin/env python3
"""Generate plausibility-sweep tasks -> data/sweep_tasks.json.

Usage: python make_sweep.py --seed 0 --n_per_field 10 [--factors 0.9 0.75 0.5 0.25 0.1 0.02 0.005]
"""
import argparse
import json
import sys
from pathlib import Path

from tasks import SWEEP_FACTORS, generate_sweep_tasks, verify_task
from tools import ProteinTable

OUT = Path(__file__).parent / "data" / "sweep_tasks.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_per_field", type=int, default=10)
    ap.add_argument("--factors", type=float, nargs="+", default=SWEEP_FACTORS)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    table = ProteinTable()
    tasks = generate_sweep_tasks(table.records, table.records, args.n_per_field, args.seed, args.factors)
    by_acc = {r["accession"]: r for r in table.records}
    for t in tasks:
        verify_task(t, by_acc)
    Path(args.out).write_text(json.dumps({"seed": args.seed, "n_tasks": len(tasks), "factors": args.factors,
                                          "tasks": tasks}, indent=1))
    conds = list(tasks[0]["corruptions"])
    print(f"Wrote {len(tasks)} sweep tasks x {len(conds)} corruption conditions to {args.out}", file=sys.stderr)
    print("conditions:", " ".join(conds), file=sys.stderr)


if __name__ == "__main__":
    main()
