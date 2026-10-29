"""Phase 5 step 1: sequence-version history from UniSave for the 300 benchmark proteins."""
import json, time, requests
from pathlib import Path
prots = json.load(open("data/proteins_v2.json")); prots = prots if isinstance(prots, list) else list(prots.values())
out, changed, superseded = {}, 0, 0
for i, p in enumerate(prots):
    acc = p["accession"]
    try:
        r = requests.get(f"https://rest.uniprot.org/unisave/{acc}", params={"format": "json"}, timeout=60)
        items = r.json().get("results", []) if r.status_code == 200 else []
    except Exception: items = []
    if i == 0: print("example keys:", sorted(items[0].keys()) if items else "NO ITEMS (check endpoint)", flush=True)
    sv2ev = {}
    for it in items:
        sv, ev = it.get("sequenceVersion"), it.get("entryVersion")
        if sv is not None and ev is not None: sv2ev[sv] = max(ev, sv2ev.get(sv, 0))
    out[acc] = {"n_entry_versions": len(items), "seqver_to_entryver": sv2ev}
    changed += len(sv2ev) > 1; superseded += max(0, len(sv2ev) - 1)
    if i % 50 == 49: print(f"  {i+1}/{len(prots)}: {changed} with revised sequences", flush=True)
    time.sleep(0.2)
Path("data/unisave_history.json").write_text(json.dumps(out, indent=1))
print(f"UniSave: {changed}/{len(prots)} proteins have >=2 sequence versions; {superseded} superseded sequences in total")
