"""Phase 5 analysis as pre-registered (results/phase5/PREREGISTRATION.md), then exploratory tables."""
import json, collections
from scipy.stats import fisher_exact
from harness import second_source as ss
T = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
MODELS = ["opus5", "argon", "deepseek"]; ARMS = ["full", "summary", "harness_ss1"]
rows, excl = [], collections.Counter()
for m in MODELS:
    for a in ARMS:
        seen = {}
        for l in open(f"results/phase5/{m}_{a}.jsonl"):
            t = json.loads(l); seen[t["run_key"]] = t
        for t in seen.values():
            tr = t.get("trace") or {}
            if tr.get("error"):
                excl[f"{m}/{a}/{'undelivered' if str(tr['error']).startswith('leak_check') else 'api_error'}"] += 1; continue
            if not tr.get("parsed_ok", True): excl[f"{m}/{a}/unparsed"] += 1; continue
            task = T[t["task_id"]]; c = task["corruptions"]["superseded"]
            rows.append(dict(model=m, arm=a, cond=t["condition"], correct=bool(t.get("correct")), prop=bool(t.get("propagated")),
                             flag=bool(tr.get("concerns")), direction=task["direction"], dl=abs(c["d_length"]),
                             covered=bool(ss._AF.get(task["target_accession"])), task=t["task_id"]))
out = {"excluded_runs": dict(excl)}; print("excluded runs:", dict(excl) or "none")
bad = set()
for m in MODELS:
    for a in ARMS:
        cl = [r for r in rows if r["model"] == m and r["arm"] == a and r["cond"] == "clean"]
        acc = sum(r["correct"] for r in cl) / len(cl) if cl else float("nan")
        print(f"clean accuracy {m:9s} {a:12s} {sum(r['correct'] for r in cl)}/{len(cl)}")
        if cl and acc < 0.8: bad.add((m, a))
print("cells excluded (clean accuracy < 80%):", sorted(bad) or "none"); out["cells_excluded"] = sorted(bad)
sup = [r for r in rows if r["cond"] == "superseded" and (r["model"], r["arm"]) not in bad]
def kn(g): return sum(r["prop"] for r in g), len(g)
print("\nR1: no second source, superseded propagation >= 80% in >= 5 of 6 cells")
met = 0
for m in MODELS:
    for a in ("full", "summary"):
        k, n = kn([r for r in sup if r["model"] == m and r["arm"] == a]); ok = n > 0 and k / n >= 0.8; met += ok
        print(f"  {m:9s} {a:8s} {k}/{n} = {100 * k / max(n, 1):.0f}%  {'>= 80%' if ok else '< 80%'}"); out[f"R1|{m}|{a}"] = [k, n]
print(f"  {met}/6 cells -> {'SUPPORTED' if met >= 5 else 'NOT SUPPORTED'}"); out["R1_cells"] = met
print("\nR2: second source, covered proteins, propagation <= 10% for every model")
allok = True
for m in MODELS:
    k, n = kn([r for r in sup if r["model"] == m and r["arm"] == "harness_ss1" and r["covered"]]); ok = n > 0 and k / n <= 0.10; allok &= ok
    print(f"  {m:9s} {k}/{n} = {100 * k / max(n, 1):.1f}%  {'<= 10%' if ok else '> 10%'}"); out[f"R2|{m}"] = [k, n]
print(f"  -> {'SUPPORTED' if allok else 'NOT SUPPORTED'}")
print("\nR3: second source, old record longer vs shorter (pooled across models; one-sided Fisher)")
for label, g in (("all arm-3 runs (as registered)", [r for r in sup if r["arm"] == "harness_ss1"]),
                 ("covered only (sensitivity)", [r for r in sup if r["arm"] == "harness_ss1" and r["covered"]])):
    kL, nL = kn([r for r in g if r["direction"] == "old_longer"]); kS, nS = kn([r for r in g if r["direction"] == "old_shorter"])
    _, p = fisher_exact([[kL, nL - kL], [kS, nS - kS]], alternative="greater")
    print(f"  {label}: longer {kL}/{nL} vs shorter {kS}/{nS}, p = {p:.3g} -> {'SUPPORTED' if p < 0.05 else 'NOT SUPPORTED'}")
    out[f"R3|{label}"] = [kL, nL, kS, nS, p]
print("\nExploratory: superseded propagation by |length change| (1-5 | 6-50 | >50) and flagged among propagated")
for m in MODELS:
    for a in ARMS:
        g = [r for r in sup if r["model"] == m and r["arm"] == a]
        bins = [kn([r for r in g if lo <= r["dl"] <= hi]) for lo, hi in ((1, 5), (6, 50), (51, 10 ** 6))]
        fp = sum(r["prop"] and r["flag"] for r in g); kp = sum(r["prop"] for r in g)
        print(f"  {m:9s} {a:12s} " + " | ".join(f"{k}/{n}" for k, n in bins) + f"   flagged among propagated {fp}/{kp}")
unc = [r for r in sup if not r["covered"]]
if unc: print("uncovered protein runs:", [(r["model"], r["arm"], r["task"], "propagated" if r["prop"] else "not") for r in unc])
json.dump(out, open("results/phase5/analysis.json", "w"), indent=1, default=float)
