#!/usr/bin/env python3
"""Fetch full UniProtKB JSON entries for every protein in the given tables -> data/uniprot_full.json.
Drops `references` and `uniProtKBCrossReferences` (citations and external links) to bound record size."""
import argparse, json, sys, time
from pathlib import Path
import requests

ap = argparse.ArgumentParser()
ap.add_argument("--tables", nargs="+", default=["data/proteins.json", "data/proteins_v2.json"])
ap.add_argument("--out", default="data/uniprot_full.json")
ap.add_argument("--drop", nargs="+", default=["references", "uniProtKBCrossReferences"])
args = ap.parse_args()

accs = []
for t in args.tables:
    accs += [r["accession"] for r in json.load(open(t))]
accs = list(dict.fromkeys(accs))
out = Path(args.out)
full = json.loads(out.read_text()) if out.exists() else {}
for i, acc in enumerate(accs, 1):
    if acc in full:
        continue
    for attempt in range(4):
        try:
            r = requests.get(f"https://rest.uniprot.org/uniprotkb/{acc}.json", timeout=60)
            r.raise_for_status(); e = r.json(); break
        except requests.RequestException as ex:
            if attempt == 3: raise
            time.sleep(2 * (attempt + 1))
    for k in args.drop:
        e.pop(k, None)
    full[acc] = e
    if i % 25 == 0:
        print(f"  {i}/{len(accs)}", file=sys.stderr); out.write_text(json.dumps(full))
    time.sleep(0.2)
out.write_text(json.dumps(full))
sizes = sorted(len(json.dumps(e)) for e in full.values())
print(f"wrote {len(full)} full entries to {out}; size chars median {sizes[len(sizes)//2]}, max {sizes[-1]}")
