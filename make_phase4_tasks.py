"""Phase 4: new chemistry fields by derivation-route class: monoisotopic mass (exact), TPSA (approximate), complexity (none).
Threshold tasks, one compound per task, interleaved so any prefix is balanced across field x direction.
Plausible = module SHRINK/INFLATE factor. Monoisotopic mass is scaled together with molecular weight and heavy-atom count,
so formula/SMILES are the only contradiction (Phase 1 design). Impossible = 0 / negative or absurdly large."""
import json, random
from domains import chemistry as chem
rng = random.Random(4)
pc = json.load(open("data/chem/pubchem_extra_props.json")); recs = []
for r in json.load(open("data/chem/compounds.json")):
    p = pc[str(r["cid"])]; r = dict(r); cx = float(p["Complexity"])
    r.update({"monoisotopic_mass": round(float(p["MonoisotopicMass"]), 3), "tpsa": round(float(p["TPSA"]), 1),
              "complexity": int(cx) if cx == int(cx) else round(cx, 1)})
    recs.append(r)
json.dump(recs, open("data/chem/compounds_phase4.json", "w"), indent=1)
table = chem.Table("data/chem/compounds_phase4.json"); by_acc = table.by_acc
F = {"shrink": chem.SHRINK_FACTORS, "inflate": chem.INFLATE_FACTORS}
print("plausible factors:", F)
TEMPLATE = {"monoisotopic_mass": "mono_threshold", "tpsa": "tpsa_threshold", "complexity": "complexity_threshold"}
MIN = {"monoisotopic_mass": 0, "tpsa": 20, "complexity": 50}
IMP = {"monoisotopic_mass": (0.0, 9_000_000_000.0), "tpsa": (-50.0, 50_000.0), "complexity": (-100, 10_000_000)}
def scaled(rec, field, f):
    if field == "monoisotopic_mass":
        return {"monoisotopic_mass": round(rec["monoisotopic_mass"] * f, 3), "molecular_weight": round(rec["molecular_weight"] * f, 2),
                "heavy_atom_count": max(1, int(round(rec["heavy_atom_count"] * f)))}
    return {field: round(rec[field] * f, 1) if field == "tpsa" else int(round(rec[field] * f))}
def impossible(field, d):
    v = IMP[field][0 if d == "shrink" else 1]
    if field == "monoisotopic_mass":
        return {"monoisotopic_mass": v, "molecular_weight": v, "heavy_atom_count": 0 if d == "shrink" else 50000}
    return {field: v}
N_PER = 30
pool = list(table.records); rng.shuffle(pool); used, tasks = set(), []
for i in range(N_PER):
    for d in ("shrink", "inflate"):
        for field, template in TEMPLATE.items():
            for rec in pool:
                if rec["accession"] in used or rec[field] < MIN[field]: continue
                f = rng.choice(F[d]); v = rec[field]
                th = (int(v) + int(round(v * f))) // 2 if field == "complexity" else round((v + v * f) / 2, 1)
                sc, im = scaled(rec, field, f), impossible(field, d)
                corr = {"impossible": {"fields": im, "clean_value": v, "corrupted_value": im[field], "direction": d},
                        "plausible": {"fields": sc, "clean_value": v, "corrupted_value": sc[field], "factor": f, "direction": d}}
                t = chem.assemble(template, {"accession": rec["accession"], "threshold": th}, rec["accession"], [rec["accession"]], corr, by_acc)
                if t is None: continue
                t["task_id"] = f"p4_{len(tasks):03d}"; t["direction"] = d; used.add(rec["accession"]); tasks.append(t); break
            else:
                raise SystemExit(f"ran out of compounds for {field} {d} at round {i}")
for t in tasks: chem.verify_task(t, by_acc)
json.dump({"domain": "chemistry", "proteins": "data/chem/compounds_phase4.json", "seed": 4, "phase": 4, "n_tasks": len(tasks), "tasks": tasks},
          open("data/chem/phase4_tasks.json", "w"), indent=1)
print(f"phase 4: {len(tasks)} tasks ({N_PER} per field x direction), one compound each, all verified")
