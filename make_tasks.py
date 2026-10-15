#!/usr/bin/env python3
"""Generate seeded, balanced tasks -> data/tasks.json.

Usage: python make_tasks.py --seed 0 --n_tasks 40
"""
import argparse
import collections
import json
import sys
from pathlib import Path

from tasks import generate_tasks, verify_task
from tools import ProteinTable

OUT = Path(__file__).parent / "data" / "tasks.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_tasks", type=int, default=40)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    table = ProteinTable()
    tasks = generate_tasks(table.records, table.task_records(), args.n_tasks, args.seed)
    by_acc = {r["accession"]: r for r in table.records}
    for t in tasks:
        verify_task(t, by_acc)  # asserts every corrupted-implied answer differs from gold

    Path(args.out).write_text(json.dumps({"seed": args.seed, "n_tasks": args.n_tasks, "tasks": tasks}, indent=1))
    print(f"Wrote {len(tasks)} tasks to {args.out}", file=sys.stderr)
    print("by target field:", dict(collections.Counter(t["target_field"] for t in tasks)), file=sys.stderr)
    print("by template:    ", dict(collections.Counter(t["template"] for t in tasks)), file=sys.stderr)
    print("unique targets: ", len({t["target_accession"] for t in tasks}), file=sys.stderr)


if __name__ == "__main__":
    main()
