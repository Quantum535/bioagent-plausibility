"""Robustness Part 3 analysis (ADDENDUM.md): labeled and silent replace vs Part 1 replace and annotate."""
import json, collections
from statistics import mean
from scipy.stats import wilcoxon
from harness import second_source as ss
P5 = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
M = ["opus5", "argon", "deepseek"]
ARMS = {"annotate": "p5_annotate", "replace (Part 1)": "p5_replace", "labeled": "p5_replace_labeled", "silent": "p5_replace_silent"}
def load(m, cell):
    seen = {}
    for l in open(f"results/robustness/{m}_{cell}.jsonl"):
        t = json.loads(l); seen[t["run_key"]] = t
    return [t for t in seen.values() if not (t.get("trace") or {}).get("error") and (t.get("trace") or {}).get("parsed_ok", True)]
data = {(m, a): load(m, c) for m in M for a, c in ARMS.items()}
cov = lambda t: bool(ss._AF.get(P5[t["task_id"]]["target_accession"]))
print("covered superseded propagation, pooled over samples (clean accuracy where run)")
for m in M:
    cells = []
    for a in ARMS:
        g = [t for t in data[(m, a)] if t["condition"] == "superseded" and cov(t)]; k = sum(bool(t.get("propagated")) for t in g)
        cl = [t for t in data[(m, a)] if t["condition"] == "clean"]
        cells.append(f"{a}: {k}/{len(g)} = {100 * k / max(len(g), 1):.1f}%" + (f" (clean {sum(bool(t.get('correct')) for t in cl)}/{len(cl)})" if cl else ""))
    print(f"  {m:9s} " + " | ".join(cells))
for lab, a in (("L1", "labeled"), ("S1", "silent")):
    oks = []
    for m in M:
        g = [t for t in data[(m, a)] if t["condition"] == "superseded" and cov(t)]
        oks.append(sum(bool(t.get("propagated")) for t in g) / max(len(g), 1) <= 0.02)
    print(f"{lab} ({a} <= 2% for every model): {'SUPPORTED' if all(oks) else 'NOT SUPPORTED'}")
xl, xr = [], []
for m in M:
    for tid in P5:
        a = [bool(t.get("propagated")) for t in data[(m, "labeled")] if t["task_id"] == tid and t["condition"] == "superseded"]
        b = [bool(t.get("propagated")) for t in data[(m, "replace (Part 1)")] if t["task_id"] == tid and t["condition"] == "superseded"]
        if a and b: xl.append(mean(a)); xr.append(mean(b))
try:
    _, p = wilcoxon(xl, xr, alternative="less")
    print(f"L2 labeled {mean(xl):.3f} vs Part 1 replace {mean(xr):.3f}: one-sided Wilcoxon p = {p:.2e} -> {'SUPPORTED' if p < 0.05 else 'NOT SUPPORTED'}")
except ValueError as e:
    print("L2 not computable:", e)
print("\nExploratory: reasons in propagated covered runs (heuristic on the final text)")
for m in M:
    for a in ("replace (Part 1)", "labeled", "silent"):
        g = [t for t in data[(m, a)] if t["condition"] == "superseded" and cov(t) and t.get("propagated")]
        c = collections.Counter()
        for t in g:
            x = (t["trace"].get("final_text") or "").lower()
            c["recall ('canonical')" if "canonical" in x else ("label ('observed')" if "observed" in x else "other")] += 1
        if g: print(f"  {m:9s} {a:16s} {dict(c)}  e.g. {g[0]['task_id']}: {(g[0]['trace'].get('final_text') or '').replace(chr(10), ' ')[:200]}")
