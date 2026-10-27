"""Override-boundary tasks: single-call threshold tasks in both directions, with the paired field scaled alike,
to be run with --record_format full so the sequence (proteins) or formula/SMILES (molecules) is the only contradiction."""
import json, random, sys
from pathlib import Path
import domains
from tasks import sweep_condition_name

SHRINK = [0.9, 0.8, 0.7, 0.5, 0.3, 0.1, 0.02, 0.005]
INFLATE = [1.1, 1.25, 1.5, 2, 3, 10, 50, 200]
N_PER_CELL = 20   # tasks per (field, direction) -> 40 tasks per point per direction across the two fields


def build(domain, out, seed=0):
    dom = domains.load(domain)
    table = dom.Table(dom.DEFAULT_TABLE if domain == "chemistry" else "data/proteins_v2.json")
    recs = table.records; by_acc = {r["accession"]: r for r in recs}
    if domain == "chemistry":
        from domains.chemistry import make_scaled_corruption, assemble
        fields = (("molecular_weight", "weight_threshold"), ("heavy_atom_count", "heavy_atom_threshold"))
        cands = [r for r in recs if r["heavy_atom_count"] >= 10]
    else:
        from corrupt import make_scaled_corruption
        from tasks import assemble
        fields = (("length", "length_threshold"), ("mass", "mass_threshold"))
        cands = list(recs)
    rng = random.Random(seed); rng.shuffle(cands)
    tasks, used = [], set()
    for direction, factors in (("shrink", SHRINK), ("inflate", INFLATE)):
        edge = max(factors) if direction == "shrink" else min(factors)      # threshold sits midway between true and edge*true
        for field, template in fields:
            made = 0
            for rec in cands:
                if made >= N_PER_CELL: break
                if rec["accession"] in used: continue
                true = rec[field]; params = {"accession": rec["accession"]}
                if field == "mass": params["threshold_kda"] = round(true * (1 + edge) / 2 / 1000, 1)
                elif field == "molecular_weight": params["threshold"] = round(true * (1 + edge) / 2, 1)
                else: params["threshold"] = (true + int(round(true * edge))) // 2
                corr = {sweep_condition_name(f, True): make_scaled_corruption(rec, field, f, True) for f in factors}
                t = assemble(template, params, rec["accession"], [rec["accession"]], corr, by_acc)
                if t is None: continue
                t["direction"] = direction; t["task_id"] = f"b{len(tasks):03d}"; tasks.append(t); used.add(rec["accession"]); made += 1
            assert made == N_PER_CELL, f"{domain} {direction} {field}: only {made}"
    golds = {d: sorted({t["gold"] for t in tasks if t["direction"] == d}) for d in ("shrink", "inflate")}
    Path(out).write_text(json.dumps({"seed": seed, "n_tasks": len(tasks), "domain": domain,
                                     "proteins": None if domain == "chemistry" else "data/proteins_v2.json", "tasks": tasks}, indent=1))
    print(f"{domain}: {len(tasks)} tasks -> {out}; gold by direction {golds}")
    return sorted({c for t in tasks for c in t["corruptions"]}, key=lambda c: float(c[1:].split("_")[0]))


conds = build("protein", "data/boundary_tasks.json")
conds2 = build("chemistry", "data/chem/boundary_tasks.json")
assert conds == conds2
Path("data/boundary_conditions.txt").write_text(" ".join(["clean"] + conds) + "\n")
print("conditions:", " ".join(["clean"] + conds))
