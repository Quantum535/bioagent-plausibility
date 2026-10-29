"""Phase 4b (exploratory, registered as an addendum after H2 failed): why did an exact derivation route not produce overrides?
Same 60 compounds, factors and directions as the Phase 4 monoisotopic-mass tasks; full record.
A: monoisotopic mass corrupted alone (MW and heavy atoms clean); mono question; Phase 4 table.
B: Phase-1-style: MW question; MW and heavy atoms scaled together; original table (no extra fields).
C: MW question; Phase 4 corruption (mono, MW, heavy atoms scaled together); Phase 4 table."""
import json
from domains import chemistry as chem
P4 = json.load(open("data/chem/phase4_tasks.json")); mono = [t for t in P4["tasks"] if t["target_field"] == "monoisotopic_mass"]
T4 = chem.Table("data/chem/compounds_phase4.json"); T0 = chem.Table(chem.DEFAULT_TABLE)
A, B, C = [], [], []
for t in mono:
    acc = t["target_accession"]; d = t["direction"]; p = t["corruptions"]["plausible"]; f = p["factor"]
    r4, r0 = T4.by_acc[acc], T0.by_acc[acc]
    ca = {"fields": {"monoisotopic_mass": p["fields"]["monoisotopic_mass"]}, "clean_value": r4["monoisotopic_mass"],
          "corrupted_value": p["fields"]["monoisotopic_mass"], "factor": f, "direction": d}
    a = chem.assemble("mono_threshold", dict(t["params"]), acc, [acc], {"plausible": ca}, T4.by_acc)
    mw_th = round((r0["molecular_weight"] + r0["molecular_weight"] * f) / 2, 1)
    cb = chem.make_scaled_corruption(r0, "molecular_weight", f, True); cb["direction"] = d
    b = chem.assemble("weight_threshold", {"accession": acc, "threshold": mw_th}, acc, [acc], {"plausible": cb}, T0.by_acc)
    cc = {"fields": dict(p["fields"]), "clean_value": r4["molecular_weight"], "corrupted_value": p["fields"]["molecular_weight"], "factor": f, "direction": d}
    c = chem.assemble("weight_threshold", {"accession": acc, "threshold": mw_th}, acc, [acc], {"plausible": cc}, T4.by_acc)
    for lst, task, tid in ((A, a, t["task_id"]), (B, b, t["task_id"].replace("p4_", "p4b_B_")), (C, c, t["task_id"].replace("p4_", "p4b_C_"))):
        assert task is not None, (tid, "assemble rejected")
        task["task_id"] = tid; task["direction"] = d; lst.append(task)
for name, lst, path, T in (("A", A, "data/chem/compounds_phase4.json", T4), ("B", B, chem.DEFAULT_TABLE, T0), ("C", C, "data/chem/compounds_phase4.json", T4)):
    for task in lst: chem.verify_task(task, T.by_acc)
    json.dump({"domain": "chemistry", "proteins": path, "seed": 4, "phase": "4b", "arm": name, "n_tasks": len(lst), "tasks": lst},
              open(f"data/chem/phase4b_{name}.json", "w"), indent=1)
    print(f"arm {name}: {len(lst)} tasks, table {path}")
print("B corruption example:", {k: v for k, v in B[0]["corruptions"]["plausible"].items() if k != "implied"})
