"""Phase 5: real historical UniProt errors. For each benchmark protein whose sequence was later revised with a length change,
the most recent superseded sequence becomes the 'superseded' condition: the record shows the old sequence with its own length and
mass (current annotations, features pruned to the old length, no checksums), so derivation checks pass. One task per protein."""
import json
import domains, tasks as ptasks
from harness.checks import check_protein
from harness.second_source import check_protein_ss
dom = domains.load("protein"); Ts = dom.Table("data/proteins_v2.json"); Tf = dom.Table("data/proteins_v2.json", record_format="full")
old = json.load(open("data/unisave_old_sequences.json"))
outdated = {a for a, v in old.items() if any(x["same_as_stored"] for x in v)}
tasks, skipped, ss_flags = [], {"stored_record_outdated": 0, "no_length_change": 0, "assemble_rejected": 0}, 0
for acc, versions in sorted(old.items()):
    if acc in outdated: skipped["stored_record_outdated"] += 1; continue
    cands = [x for x in versions if x["d_length"] != 0]
    if not cands: skipped["no_length_change"] += 1; continue
    x = max(cands, key=lambda v: v["seq_version"]); rec = Ts.by_acc[acc]
    assert rec.get("length") is not None and rec.get("mass") is not None, ("table record lacks length/mass", acc, sorted(rec))
    L_old, M_old = x["length"], int(round(x["mass"])); fields = {"length": L_old, "mass": M_old}
    field = "mass" if (len(tasks) % 2 == 1 and abs(M_old - rec["mass"]) >= 200) else "length"
    params = {"accession": acc}
    if field == "length": params["threshold"] = (rec["length"] + L_old) // 2
    else: params["threshold_kda"] = round((rec["mass"] + M_old) / 2 / 1000, 1)
    corr = {"fields": fields, "clean_value": rec[field], "corrupted_value": fields[field], "coherent": True, "real": True,
            "full_patch": {"sequence": x["sequence"], "mass": M_old}, "seq_version": x["seq_version"], "entry_version": x["entry_version"],
            "d_length": x["d_length"], "direction": "old_longer" if x["d_length"] > 0 else "old_shorter"}
    t = ptasks.assemble(f"{field}_threshold", params, acc, [acc], {"superseded": corr}, Ts.by_acc)
    if t is None: skipped["assemble_rejected"] += 1; continue
    t["task_id"] = f"r{len(tasks):03d}"; t["direction"] = corr["direction"]
    s_rec = json.loads(dom.render(Ts, rec, corr)); f_rec = json.loads(dom.render(Tf, rec, corr))
    v = check_protein(s_rec, Ts, full=f_rec)
    assert all(v[k]["status"] == "ok" for k in ("length", "mass")), ("derivation check not fooled", acc, v)
    ss_flags += check_protein_ss(acc, s_rec)[field]["status"] == "mismatch"
    tasks.append(t)
base = json.load(open("data/tasks_v2.json"))
json.dump(dict(base, phase=5, n_tasks=len(tasks), tasks=tasks), open("data/phase5_tasks.json", "w"), indent=1)
d = [abs(t["corruptions"]["superseded"]["d_length"]) for t in tasks]
print(f"phase 5: {len(tasks)} tasks | fields {dict((f, sum(t['target_field'] == f for t in tasks)) for f in ('length', 'mass'))}"
      f" | directions {dict((k, sum(t['direction'] == k for t in tasks)) for k in ('old_longer', 'old_shorter'))}")
print(f"|length change| 1-5: {sum(x <= 5 for x in d)}, 6-50: {sum(5 < x <= 50 for x in d)}, >50: {sum(x > 50 for x in d)} | skipped {skipped}")
print(f"derivation checks fooled on all {len(tasks)}; second source (AlphaFold) flags the target field on {ss_flags}/{len(tasks)}")
