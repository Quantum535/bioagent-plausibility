"""Coherent corruption for the full-record format: edit the sequence (proteins) or swap the structure (molecules) and
recompute every derived field, so derivation checks pass and only a second source or recall can catch it."""
import json, random
from Bio.SeqUtils import molecular_weight
import domains, tasks as ptasks
from domains import chemistry as chem
from matching import match_answer

rng = random.Random(0)
# ---------------- proteins
full = json.load(open("data/uniprot_full.json")); full = {r["primaryAccession"]: r for r in (full.values() if isinstance(full, dict) else full)}
pt = json.load(open("data/tasks_v2.json")); by_acc = {r["accession"]: r for r in domains.load("protein").Table("data/proteins_v2.json").records}
def coherent_protein(t, kind):
    acc = t["target_accession"]; seq = full[acc]["sequence"]["value"]; f = t["corruptions"]["plausible"].get("factor")
    if kind == "impossible":
        if t["direction"] != "shrink": return None
        new = seq[:3]
    else:
        L = max(3, int(round(len(seq) * f)))
        new = seq[:L] if L <= len(seq) else (seq + (seq[-60:] * 40))[:L]
    mass = int(round(molecular_weight(new, seq_type="protein")))
    return {"fields": {"length": len(new), "mass": mass}, "clean_value": t["corruptions"]["impossible"]["clean_value"],
            "corrupted_value": {"length": len(new), "mass": mass}[t["target_field"]], "factor": None if kind == "impossible" else f,
            "full_patch": {"sequence": new, "mass": mass}, "coherent": True}
out, kept = [], {"shrink": [], "inflate": []}
for t in pt["tasks"]:
    if t["target_field"] not in ("length", "mass"): continue
    t = json.loads(json.dumps(t)); ok = True
    for kind in ("impossible", "plausible"):
        c = coherent_protein(t, kind)
        if c is None: continue
        t["corruptions"][f"coherent_{kind}"] = c
        implied = ptasks.TEMPLATES[t["template"]]["compute"](t, ptasks.records_for(t, by_acc, f"coherent_{kind}"))
        if match_answer(implied, t["gold"], t["answer_type"]): ok = False
        c["implied"] = implied
    if ok: kept[t["direction"]].append(t)
for d, ts in kept.items():
    json.dump(dict(pt, n_tasks=len(ts), tasks=ts), open(f"data/coherent_{d}.json", "w"), indent=1)
    print(f"protein coherent_{d}: {len(ts)} tasks; conditions {sorted(set(k for t in ts for k in t['corruptions'] if k.startswith('coherent')))}")
# ---------------- chemistry: structure swap
ct = json.load(open("data/chem/tasks.json")); table = chem.Table(chem.DEFAULT_TABLE); cby = table.by_acc
def coherent_chem(t, kind):
    A = cby[t["target_accession"]]
    if kind == "impossible":
        if t["direction"] != "shrink": return None
        B = {"molecular_weight": 16.04, "heavy_atom_count": 1, "h_bond_donors": 0, "smiles": "C", "formula": "CH4", "iupac_name": "methane"}
    else:
        f = t["corruptions"]["plausible"]["factor"]; lo, hi = (0.72, 0.83) if f < 1 else (1.17, 1.28)
        cands = [r for r in table.records if r["accession"] != A["accession"] and lo <= r["molecular_weight"] / A["molecular_weight"] <= hi]
        if not cands: return None
        B = rng.choice(cands)
    fields = {k: B[k] for k in ("molecular_weight", "heavy_atom_count", "h_bond_donors", "smiles", "formula", "iupac_name")}
    return {"fields": fields, "clean_value": A[t["target_field"]], "corrupted_value": B[t["target_field"]], "coherent": True, "swap_source": B.get("cid")}
kept = {"shrink": [], "inflate": []}
for t in ct["tasks"]:
    if t["target_field"] not in ("molecular_weight", "heavy_atom_count"): continue
    t = json.loads(json.dumps(t)); ok = True
    for kind in ("impossible", "plausible"):
        c = coherent_chem(t, kind)
        if c is None: continue
        t["corruptions"][f"coherent_{kind}"] = c
        implied = chem.TEMPLATES[t["template"]]["compute"](t, chem.records_for(t, cby, f"coherent_{kind}"))
        if match_answer(implied, t["gold"], t["answer_type"]) or (t["n_calls_expected"] == 2 and not chem.TEMPLATES[t["template"]]["margin"](t, chem.records_for(t, cby, f"coherent_{kind}"))): ok = False
        c["implied"] = implied
    if ok and any(k.startswith("coherent") for k in t["corruptions"]): kept[t["direction"]].append(t)
for d, ts in kept.items():
    json.dump(dict(ct, n_tasks=len(ts), tasks=ts), open(f"data/chem/coherent_{d}.json", "w"), indent=1)
    print(f"chemistry coherent_{d}: {len(ts)} tasks")
