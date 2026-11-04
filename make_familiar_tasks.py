"""Familiar duplicate field: as the repetition arms, with the repeat under a standard-looking name (average_mass, by definition the molecular weight).
F1: weight and average_mass scaled together (a familiar repeat agrees). F2: only the weight scaled (a familiar repeat disagrees)."""

import json
from domains import chemistry as chem
P4 = json.load(open("data/chem/phase4_tasks.json")); mono = [t for t in P4["tasks"] if t["target_field"] == "monoisotopic_mass"]
comps = json.load(open(chem.DEFAULT_TABLE))
for c in comps: c["average_mass"] = c["molecular_weight"]
json.dump(comps, open("data/chem/compounds_fam.json", "w"), indent=1)
T0, TR = chem.Table(chem.DEFAULT_TABLE), chem.Table("data/chem/compounds_fam.json")
arms = {"F1": ([], "data/chem/compounds_fam.json", TR), "F2": ([], "data/chem/compounds_fam.json", TR)}
for t in mono:
    acc, d, f = t["target_accession"], t["direction"], t["corruptions"]["plausible"]["factor"]
    r0 = T0.by_acc[acc]; w = round(r0["molecular_weight"] * f, 2); th = round((r0["molecular_weight"] + w) / 2, 1)
    c0 = chem.make_scaled_corruption(r0, "molecular_weight", f, False); c0["direction"] = d
    c1 = {"fields": {"molecular_weight": w, "average_mass": w}, "clean_value": r0["molecular_weight"], "corrupted_value": w, "factor": f, "direction": d}
    c2 = {"fields": {"molecular_weight": w}, "clean_value": r0["molecular_weight"], "corrupted_value": w, "factor": f, "direction": d}
    for name, corr in (("F1", c1), ("F2", c2)):
        lst, path, T = arms[name]
        task = chem.assemble("weight_threshold", {"accession": acc, "threshold": th}, acc, [acc], {"plausible": corr}, T.by_acc)
        assert task is not None, (name, acc); task["task_id"] = t["task_id"].replace("p4_", f"fam_{name}_"); task["direction"] = d; lst.append(task)
for name, (lst, path, T) in arms.items():
    for task in lst: chem.verify_task(task, T.by_acc)
    json.dump({"domain": "chemistry", "proteins": path, "seed": 4, "phase": "repetition", "arm": name, "n_tasks": len(lst), "tasks": lst}, open(f"data/chem/phase4b_{name}.json", "w"), indent=1)
    print(f"arm {name}: {len(lst)} tasks, table {path}")
