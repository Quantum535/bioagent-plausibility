#!/usr/bin/env python3
"""Fetch reviewed (Swiss-Prot) human proteins from the UniProt REST API.

Writes data/proteins.json: a seeded random sample of real records with the
fields the experiment needs. Nothing here is hand-written; if the fetch fails
the script exits non-zero.

Usage: python fetch_data.py --seed 0 [--n_sample 60] [--pool_size 3000] [--refresh]
"""
import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

import requests

UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/search"
QUERY = "(reviewed:true) AND (organism_id:9606) AND (length:[150 TO 1500])"
FIELDS = "accession,protein_name,gene_primary,organism_name,length,mass,cc_subcellular_location"
DATA_DIR = Path(__file__).parent / "data"
POOL_PATH = DATA_DIR / "uniprot_pool.json"
OUT_PATH = DATA_DIR / "proteins.json"


def _next_link(headers):
    link = headers.get("Link", "")
    m = re.search(r'<([^>]+)>;\s*rel="next"', link)
    return m.group(1) if m else None


def fetch_pool(pool_size, page_size=500):
    """Page through UniProt until pool_size raw entries are collected."""
    entries = []
    url = UNIPROT_URL
    params = {"query": QUERY, "fields": FIELDS, "format": "json", "size": page_size}
    while len(entries) < pool_size and url:
        for attempt in range(4):
            try:
                r = requests.get(url, params=params if url == UNIPROT_URL else None, timeout=60)
                r.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == 3:
                    raise
                print(f"  retry {attempt + 1} after error: {e}", file=sys.stderr)
                time.sleep(2 * (attempt + 1))
        body = r.json()
        page = body.get("results", [])
        if not page:
            break
        entries.extend(page)
        print(f"  fetched {len(entries)} entries", file=sys.stderr)
        url = _next_link(r.headers)
    return entries[:pool_size]


def parse_entry(e):
    """Extract the 7 experiment fields from a raw UniProtKB JSON entry. Returns None if any is missing."""
    try:
        accession = e["primaryAccession"]
        desc = e.get("proteinDescription", {})
        name = (desc.get("recommendedName") or {}).get("fullName", {}).get("value")
        if not name and desc.get("submissionNames"):
            name = desc["submissionNames"][0].get("fullName", {}).get("value")
        genes = e.get("genes") or []
        gene = (genes[0].get("geneName") or {}).get("value") if genes else None
        organism = (e.get("organism") or {}).get("scientificName")
        seq = e.get("sequence") or {}
        length = seq.get("length")
        mass = seq.get("molWeight")
        loc = None
        for c in e.get("comments") or []:
            if c.get("commentType") == "SUBCELLULAR LOCATION":
                locs = c.get("subcellularLocations") or []
                if locs and locs[0].get("location", {}).get("value"):
                    loc = locs[0]["location"]["value"]
                    break
    except (KeyError, TypeError, AttributeError):
        return None
    rec = {
        "accession": accession,
        "protein_name": name,
        "gene_symbol": gene,
        "organism": organism,
        "length": length,
        "mass": mass,
        "subcellular_location": loc,
    }
    if any(v in (None, "") for v in rec.values()):
        return None
    if not isinstance(length, int) or not isinstance(mass, int):
        return None
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--n_sample", type=int, default=60)
    ap.add_argument("--n_task", type=int, default=40, help="how many of the sample are marked for tasks; rest are spare")
    ap.add_argument("--pool_size", type=int, default=3000)
    ap.add_argument("--refresh", action="store_true", help="re-download even if the raw pool is cached")
    args = ap.parse_args()
    DATA_DIR.mkdir(exist_ok=True)

    if POOL_PATH.exists() and not args.refresh:
        raw = json.loads(POOL_PATH.read_text())
        print(f"Using cached raw pool: {len(raw)} entries ({POOL_PATH})", file=sys.stderr)
    else:
        print(f"Querying UniProt: {QUERY}", file=sys.stderr)
        raw = fetch_pool(args.pool_size)
        if len(raw) < args.n_sample * 5:
            print(f"ERROR: UniProt fetch returned only {len(raw)} entries; aborting.", file=sys.stderr)
            sys.exit(1)
        POOL_PATH.write_text(json.dumps(raw))
        print(f"Saved raw pool ({len(raw)} entries) to {POOL_PATH}", file=sys.stderr)

    parsed = [p for p in (parse_entry(e) for e in raw) if p is not None]
    parsed = [p for p in parsed if p["organism"] == "Homo sapiens"]
    # keep gene symbols unique so find_protein_by_gene is unambiguous
    seen, uniq = set(), []
    for p in sorted(parsed, key=lambda r: r["accession"]):
        if p["gene_symbol"].upper() in seen:
            continue
        seen.add(p["gene_symbol"].upper())
        uniq.append(p)
    print(f"Complete human records with unique gene symbols: {len(uniq)} / {len(raw)}", file=sys.stderr)
    if len(uniq) < args.n_sample:
        print("ERROR: not enough complete records; aborting.", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(args.seed)
    sample = rng.sample(uniq, args.n_sample)
    for i, rec in enumerate(sample):
        rec["split"] = "task" if i < args.n_task else "spare"
    OUT_PATH.write_text(json.dumps(sample, indent=1))
    print(f"Wrote {len(sample)} proteins ({args.n_task} task / {args.n_sample - args.n_task} spare) to {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
