"""Robustness analysis as written in results/robustness/ADDENDUM.md (Part 1: replace + second source; Part 2: repeatability)."""
import json, glob, collections
from statistics import mean
from scipy.stats import wilcoxon, fisher_exact
from harness import second_source as ss
P5 = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
O = "results/robustness"; rows, excl = [], collections.Counter()
for f in sorted(glob.glob(f"{O}/*.jsonl")):
    m, cell = f.split("/")[-1][:-6].split("_", 1)
    seen = {}
    for l in open(f):
        t = json.loads(l); seen[t["run_key"]] = t
    for t in seen.values():
        tr = t.get("trace") or {}
        if tr.get("error"): excl[f"{m}/{cell}/error"] += 1; continue
        if not tr.get("parsed_ok", True): excl[f"{m}/{cell}/unparsed"] += 1; continue
        task = P5.get(t["task_id"]) if cell.startswith("p5") else None
        rows.append(dict(m=m, cell=cell, cond=t["condition"], s=int(t.get("sample") or 0), task=t["task_id"], prop=bool(t.get("propagated")),
                         correct=bool(t.get("correct")), direction=task["direction"] if task else None,
                         covered=bool(ss._AF.get(task["target_accession"])) if task else None))
def sel(**kw): return [r for r in rows if all(r[k] == v for k, v in kw.items())]
def kn(g): return sum(r["prop"] for r in g), len(g)
def unanimous(g):
    by = collections.defaultdict(list)
    for r in g: by[r["task"]].append(r["prop"])
    full = [v for v in by.values() if len(v) == 3]; return sum(len(set(v)) == 1 for v in full), len(full)
out = {"excluded": dict(excl)}; print("excluded runs:", dict(excl) or "none")
M5 = ["opus5", "argon", "deepseek"]; M4 = ["opus5", "argon", "flash", "deepseek"]
print("\n== Part 1: replace + second source, Phase 5 ==")
ok_all = True
for m in M5:
    cl = sel(m=m, cell="p5_replace", cond="clean"); k, n = kn(sel(m=m, cell="p5_replace", cond="superseded", covered=True)); ok = n > 0 and k / n <= 0.02; ok_all &= ok
    kr, nr = kn(sel(m=m, cell="p5_replace", cond="superseded"))
    print(f"  {m:9s} clean {sum(r['correct'] for r in cl)}/{len(cl)} | RR1 covered superseded {k}/{n} = {100 * k / max(n, 1):.1f}% {'<= 2%' if ok else '> 2%'}"
          f" | restored original value (all tasks) {kr}/{nr}")
    out[f"RR1|{m}"] = [k, n]
print(f"  RR1 -> {'SUPPORTED' if ok_all else 'NOT SUPPORTED'}")
xr, xa = [], []
for m in M5:
    for tid in P5:
        a = [r["prop"] for r in sel(m=m, cell="p5_annotate", cond="superseded", task=tid)]
        b = [r["prop"] for r in sel(m=m, cell="p5_replace", cond="superseded", task=tid)]
        if a and b: xa.append(mean(a)); xr.append(mean(b))
try:
    _, p = wilcoxon(xr, xa, alternative="less"); print(f"  RR2 replace {mean(xr):.3f} vs annotate {mean(xa):.3f} (mean per model x task), one-sided Wilcoxon p = {p:.2e} -> {'SUPPORTED' if p < 0.05 else 'NOT SUPPORTED'}")
    out["RR2"] = [mean(xr), mean(xa), p]
except ValueError as e:
    print("  RR2 not computable:", e); out["RR2"] = str(e)
print("\n== Part 2: repeatability (3 samples) ==")
print("Phase 5 full record, superseded: per-sample propagation (R1 >= 80%?) | tasks unanimous across samples")
for m in M5:
    g = sel(m=m, cell="p5_full", cond="superseded"); u, nu = unanimous(g)
    print(f"  {m:9s} " + "  ".join(f"s{s}: {kn([r for r in g if r['s'] == s])[0]}/{kn([r for r in g if r['s'] == s])[1]}" for s in range(3)) + f" | unanimous {u}/{nu}")
print("Phase 5 annotate + second source, covered superseded: per-sample propagation (R2 <= 10%?) | unanimous")
for m in M5:
    g = sel(m=m, cell="p5_annotate", cond="superseded", covered=True); u, nu = unanimous(g)
    print(f"  {m:9s} " + "  ".join(f"s{s}: {kn([r for r in g if r['s'] == s])[0]}/{kn([r for r in g if r['s'] == s])[1]}" for s in range(3)) + f" | unanimous {u}/{nu}")
print("R3 per sample (annotate, all runs, pooled across models): longer vs shorter, one-sided Fisher")
for s in range(3):
    g = [r for r in sel(cell="p5_annotate", cond="superseded") if r["s"] == s]
    kL, nL = kn([r for r in g if r["direction"] == "old_longer"]); kS, nS = kn([r for r in g if r["direction"] == "old_shorter"])
    _, p = fisher_exact([[kL, nL - kL], [kS, nS - kS]], alternative="greater"); print(f"  s{s}: {kL}/{nL} vs {kS}/{nS}, p = {p:.3g}")
print("Phase 4b: per-sample propagation P4 | A | B | C, with E2 (C > B) and E3 (A < P4) signs | unanimous per arm")
for m in M4:
    for s in range(3):
        r = {a: kn([x for x in sel(m=m, cell=f"4b_{a}", cond="plausible") if x["s"] == s]) for a in ("P4", "A", "B", "C")}
        rate = {a: k / n if n else float("nan") for a, (k, n) in r.items()}
        print(f"  {m:9s} s{s}: " + " | ".join(f"{a} {k}/{n}" for a, (k, n) in r.items())
              + f"   E2 {'+' if rate['C'] > rate['B'] else ('=' if rate['C'] == rate['B'] else '-')}  E3 {'+' if rate['A'] < rate['P4'] else ('=' if rate['A'] == rate['P4'] else '-')}")
    print(f"  {m:9s} unanimous: " + "  ".join(f"{a} {unanimous(sel(m=m, cell=f'4b_{a}', cond='plausible'))[0]}/{unanimous(sel(m=m, cell=f'4b_{a}', cond='plausible'))[1]}" for a in ("P4", "A", "B", "C")))
json.dump(out, open(f"{O}/analysis.json", "w"), indent=1, default=float)
