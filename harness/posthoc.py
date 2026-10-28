"""What the deterministic harness would have done on every benchmark record, joined to what the models did."""
import json, re, sys
from collections import defaultdict
sys.path.insert(0, ".")
import domains
from analysis import load_runs, score
from harness.checks import check_protein, check_compound

DOMS = {"protein": ("data/tasks_v2.json", "data/proteins_v2.json", check_protein, ["length", "mass", "organism", "gene_symbol"]),
        "chemistry": ("data/chem/tasks.json", "data/chem/compounds.json", check_compound, ["molecular_weight", "heavy_atom_count", "h_bond_donors", "name"])}
norm = lambda m: re.sub(r"^claude-", "", m.split(":")[-1].split("/")[-1].lower())
verdict = {}   # (domain, task, cond, mode) -> (target detected?, any false alarm fields)
for dname, (tfile, pfile, check, fields) in DOMS.items():
    dom = domains.load(dname); T_s = dom.Table(pfile, record_format="summary"); T_f = dom.Table(pfile, record_format="full")
    tasks = json.load(open(tfile))["tasks"]
    for t in tasks:
        acc = t["target_accession"]; rec = T_s.by_acc[acc]
        for cond in ("clean", "impossible", "plausible"):
            corr = None if cond == "clean" else t["corruptions"][cond]
            s_rec = json.loads(dom.render(T_s, rec, corr)); f_rec = json.loads(dom.render(T_f, rec, corr))
            for mode, full in (("summary", None), ("full", f_rec)):
                v = check(s_rec, T_s, full=full)
                bad = {f for f, r in v.items() if r.get("status") in ("mismatch", "not_found")}
                verdict[(dname, t["task_id"], cond, mode)] = (t["target_field"] in bad, bad - {t["target_field"]} if cond != "clean" else bad)

print("== Harness detection of the corrupted field (% of tasks), and false alarms on clean records")
for dname, (tfile, _, _, fields) in DOMS.items():
    tasks = json.load(open(tfile))["tasks"]
    print(f"-- {dname}")
    print(f"   {'field':18s} {'impossible: summary / full':>28s}   {'plausible: summary / full':>27s}   clean false alarm (summary / full)")
    for f in fields:
        ts = [t for t in tasks if t["target_field"] == f]
        det = lambda cond, mode: 100 * sum(verdict[(dname, t["task_id"], cond, mode)][0] for t in ts) / len(ts)
        fa = lambda mode: 100 * sum(bool(verdict[(dname, t["task_id"], "clean", mode)][1]) for t in ts) / len(ts)
        print(f"   {f:18s} {det('impossible','summary'):10.0f}% / {det('impossible','full'):4.0f}%   {det('plausible','summary'):12.0f}% / {det('plausible','full'):4.0f}%   {fa('summary'):8.0f}% / {fa('full'):4.0f}%")

print("\n== Of values the models actually propagated, share the harness would have flagged (with full record fetched)")
runs = defaultdict(list)
for dname, globs, fmt in (("protein", ["results/v2/traces_*.jsonl"], "summary"), ("chemistry", ["results/chem/traces_*.jsonl"], "summary"),
                          ("protein", ["results/v2_full/traces_*.jsonl"], "full"), ("chemistry", ["results/chem_full/traces_*.jsonl"], "full")):
    for r in load_runs(globs):
        s = score(r)
        if s["verify_prompt"] or s["base_condition"] == "clean" or not s["propagated"]: continue
        runs[(dname, fmt, s["base_condition"])].append(verdict[(dname, s["task_id"], s["base_condition"], "full")][0])
for key in sorted(runs):
    v = runs[key]; print(f"   {key[0]:10s} agent saw {key[1]:7s} record, {key[2]:10s}: {sum(v)}/{len(v)} propagated values catchable ({100*sum(v)/len(v):.0f}%)")
