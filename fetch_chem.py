#!/usr/bin/env python3
"""Fetch small-molecule records from PubChem PUG REST -> data/chem/compounds.json.

Scans CIDs 1..--cid_max in batches, keeps single-component molecules with a common name (Title),
weight in [--mw_min, --mw_max] and a molecular formula; draws a seeded sample. Nothing hand-written.
Usage: python fetch_chem.py --seed 0 --n_sample 300 --n_task 240
"""
import argparse, json, random, sys, time
from pathlib import Path
import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cids}/property/{props}/JSON"
PROPS = ["Title", "IUPACName", "MolecularFormula", "MolecularWeight", "HeavyAtomCount",
         "HBondDonorCount", "HBondAcceptorCount", "XLogP"]
DATA_DIR = Path(__file__).parent / "data" / "chem"
POOL_PATH = DATA_DIR / "pubchem_pool.json"
OUT_PATH = DATA_DIR / "compounds.json"


def smiles_prop():
    """PubChem renamed the SMILES property in 2025; find which name this server accepts."""
    for name in ("SMILES", "CanonicalSMILES", "ConnectivitySMILES"):
        r = requests.get(BASE.format(cids="2244", props=name), timeout=30)
        if r.ok:
            return name
    raise RuntimeError("no SMILES property name accepted")


def fetch_pool(cid_max, batch=100):
    sp = smiles_prop()
    props = ",".join(PROPS + [sp])
    pool = {}
    for start in range(1, cid_max + 1, batch):
        cids = ",".join(str(c) for c in range(start, min(start + batch, cid_max + 1)))
        for attempt in range(4):
            try:
                r = requests.get(BASE.format(cids=cids, props=props), timeout=60)
                if r.status_code == 404:  # whole batch missing
                    rows = []
                    break
                r.raise_for_status()
                rows = r.json().get("PropertyTable", {}).get("Properties", [])
                break
            except requests.RequestException as e:
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
        for p in rows:
            p["SMILES_"] = p.get(sp)
            pool[p["CID"]] = p
        if (start // batch) % 20 == 0:
            print(f"  scanned {start + batch - 1}/{cid_max}, kept {len(pool)}", file=sys.stderr)
        time.sleep(0.25)  # PubChem asks for <= 5 requests/s
    return pool


def parse(p):
    try:
        rec = {
            "cid": int(p["CID"]),
            "name": p.get("Title"),
            "iupac_name": p.get("IUPACName"),
            "formula": p.get("MolecularFormula"),
            "molecular_weight": float(p["MolecularWeight"]) if p.get("MolecularWeight") not in (None, "") else None,
            "heavy_atom_count": int(p["HeavyAtomCount"]) if p.get("HeavyAtomCount") is not None else None,
            "smiles": p.get("SMILES_"),
            "h_bond_donors": int(p["HBondDonorCount"]) if p.get("HBondDonorCount") is not None else None,
        }
    except (KeyError, TypeError, ValueError):
        return None
    if any(v in (None, "") for v in rec.values()):
        return None
    if "." in rec["smiles"] or "+" in rec["smiles"] or "-]" in rec["smiles"]:  # salts / ions
        return None
    n = rec["name"]
    if (any(ch.isdigit() for ch in n) or any(ch in n for ch in "(),[]") or len(n) > 24
            or len(n.split()) > 2):  # keep common names (aspirin, caffeine), drop systematic ones
        return None
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_sample", type=int, default=300)
    ap.add_argument("--n_task", type=int, default=240)
    ap.add_argument("--cid_max", type=int, default=30000)
    ap.add_argument("--mw_min", type=float, default=100.0)
    ap.add_argument("--mw_max", type=float, default=900.0)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if POOL_PATH.exists() and not args.refresh:
        pool = json.loads(POOL_PATH.read_text())
        print(f"Using cached pool: {len(pool)} entries", file=sys.stderr)
    else:
        pool = fetch_pool(args.cid_max)
        POOL_PATH.write_text(json.dumps(pool))
        print(f"Saved raw pool ({len(pool)} entries) to {POOL_PATH}", file=sys.stderr)

    parsed = [r for r in (parse(p) for p in pool.values()) if r]
    parsed = [r for r in parsed if args.mw_min <= r["molecular_weight"] <= args.mw_max]
    seen, uniq = set(), []
    for r in sorted(parsed, key=lambda r: r["cid"]):
        key = r["name"].lower()
        if key in seen:
            continue
        seen.add(key); uniq.append(r)
    print(f"Usable single-component named compounds in range: {len(uniq)}", file=sys.stderr)
    if len(uniq) < args.n_sample:
        sys.exit("not enough compounds; raise --cid_max")
    rng = random.Random(args.seed)
    sample = rng.sample(uniq, args.n_sample)
    for i, rec in enumerate(sample):
        rec["split"] = "task" if i < args.n_task else "spare"
    Path(args.out).write_text(json.dumps(sample, indent=1))
    print(f"Wrote {len(sample)} compounds to {args.out}", file=sys.stderr)
    for r in sample[:3]:
        print("  e.g.", {k: r[k] for k in ("cid", "name", "formula", "molecular_weight", "heavy_atom_count")}, file=sys.stderr)


if __name__ == "__main__":
    main()
