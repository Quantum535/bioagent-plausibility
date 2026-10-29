"""Phase 4b analysis as written in results/phase4/ADDENDUM_4b.md (exploratory).
Exclusions as in Phase 4: API errors, unparsed answers, model x arm cells with clean accuracy < 80%.
Arm C has no clean condition; its exclusion check uses arm B's molecular-weight clean accuracy."""
import json, collections
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import fisher_exact, norm
MODELS = ["opus5", "sonnet5", "argon", "flash", "deepseek"]; FIT = ["opus5", "argon", "flash", "deepseek"]
direction = {t["task_id"]: t["direction"] for f in ("data/chem/phase4_tasks.json", "data/chem/phase4b_A.json", "data/chem/phase4b_B.json",
             "data/chem/phase4b_C.json") for t in json.load(open(f))["tasks"]}
rows, excl = [], collections.Counter()
def load(path, arm, m, only_mono=False):
    seen = {}
    for l in open(path):
        t = json.loads(l); seen[t["run_key"]] = t
    for t in seen.values():
        if only_mono and t["target_field"] != "monoisotopic_mass": continue
        tr = t.get("trace") or {}
        if tr.get("error"): excl[f"{m}/{arm}/api_error"] += 1; continue
        if not tr.get("parsed_ok", True): excl[f"{m}/{arm}/unparsed"] += 1; continue
        rows.append({"model": m, "arm": arm, "condition": t["condition"], "direction": direction[t["task_id"]],
                     "correct": int(bool(t.get("correct"))), "prop": int(bool(t.get("propagated"))), "flag": int(bool(tr.get("concerns")))})
for m in MODELS:
    load(f"results/phase4/{m}_full.jsonl", "P4", m, only_mono=True)
    for arm in "ABC": load(f"results/phase4b/{m}_{arm}.jsonl", arm, m)
df = pd.DataFrame(rows); out = {"excluded_runs": dict(excl)}
print("excluded runs:", dict(excl) or "none")
ca = df[df.condition == "clean"].groupby(["model", "arm"]).correct.mean()
print("clean accuracy by model x arm (C uses B):", {f"{m}/{a}": round(v, 2) for (m, a), v in ca.items()})
bad = {(m, a) for (m, a), v in ca.items() if v < 0.8}; bad |= {(m, "C") for (m, a) in list(bad) if a == "B"}
print("cells excluded for clean accuracy < 80%:", sorted(bad) or "none"); out["cells_excluded"] = sorted(bad)
pl = df[(df.condition == "plausible") & ~df.apply(lambda r: (r.model, r.arm) in bad, axis=1)]
print("\nplausible propagation k/n (flagged among propagated)")
print("  model     | P4 mono (3 fields scaled) | A mono alone | B Phase-1-style MW | C MW, 3 fields scaled")
for m in MODELS:
    cells = []
    for arm in ("P4", "A", "B", "C"):
        g = pl[(pl.model == m) & (pl.arm == arm)]; k = int(g.prop.sum()); fk = int((g.prop & g.flag).sum())
        cells.append(f"{k}/{len(g)} ({fk})"); out[f"{m}|{arm}"] = [k, int(len(g)), fk]
    print(f"  {m:9s} | " + " | ".join(cells))
pred = json.load(open("results/phase4/predictions_mono.json")); passes = 0
print("\nE1: arm B (Phase-1-style) vs Phase 1 prediction intervals")
for m in MODELS:
    for d in ("shrink", "inflate"):
        g = pl[(pl.model == m) & (pl.arm == "B") & (pl.direction == d)]
        p, lo, hi = pred[f"{m}|{d}"]; obs = g.prop.mean() if len(g) else float("nan"); ok = bool(lo <= obs <= hi); passes += ok
        print(f"  {m:9s} {d:8s} predicted {100 * p:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]  observed {int(g.prop.sum())}/{len(g)} = {100 * obs:.0f}%  {'inside' if ok else 'OUTSIDE'}")
        out[f"E1|{m}|{d}"] = {"pred": [p, lo, hi], "obs": [int(g.prop.sum()), int(len(g))], "inside": ok}
print(f"  {passes}/10 inside -> {'met' if passes >= 8 else 'not met'}"); out["E1_passes"] = passes
def logit_test(data, label, sign):
    try:
        f = smf.logit("prop ~ x + C(model) + C(direction)", data=data).fit(disp=0)
        b, s = f.params["x"], f.bse["x"]
        if not f.mle_retvals.get("converged", True) or s > 50: raise ValueError(f"did not converge or separation (SE {s:.0f})")
        z = b / s; p = norm.sf(z) if sign > 0 else norm.cdf(z)
        print(f"  {label}: coefficient {b:.3f} (SE {s:.3f}), one-sided p = {p:.2e} -> {'met' if p < 0.05 else 'not met'}")
        return {"coef": b, "se": s, "p": p}
    except Exception as e:
        print(f"  {label}: regression not estimable ({e}); the per-model Fisher tests are the result"); return {"error": str(e)}
print("\nE2 / E3: logit prop ~ arm + model + direction (Opus, Argon, Flash, DeepSeek)")
d2 = pl[pl.model.isin(FIT) & pl.arm.isin(["B", "C"])].assign(x=lambda d: (d.arm == "C").astype(int))
d3 = pl[pl.model.isin(FIT) & pl.arm.isin(["A", "P4"])].assign(x=lambda d: (d.arm == "A").astype(int))
out["E2"] = logit_test(d2, "E2, C > B (extra agreeing field)", +1)
out["E3"] = logit_test(d3, "E3, A < P4 (mono alone)", -1)
tests = []
for m in FIT:
    for lab, a1, a2, alt in (("E2 C>B", "C", "B", "greater"), ("E3 A<P4", "A", "P4", "less")):
        x = pl[(pl.model == m) & (pl.arm == a1)].prop; y = pl[(pl.model == m) & (pl.arm == a2)].prop
        _, p = fisher_exact([[int(x.sum()), len(x) - int(x.sum())], [int(y.sum()), len(y) - int(y.sum())]], alternative=alt)
        tests.append([lab, m, int(x.sum()), len(x), int(y.sum()), len(y), p])
order = sorted(range(len(tests)), key=lambda i: tests[i][-1]); run = 0
for r, i in enumerate(order):
    run = max(run, min(1.0, (len(tests) - r) * tests[i][-1])); tests[i].append(run)
print("Per-model Fisher (one-sided), Holm across 8")
for lab, m, k1, n1, k2, n2, p, ph in tests:
    print(f"  {lab:8s} {m:9s} {k1}/{n1} vs {k2}/{n2}: p {p:.3g}, Holm {ph:.3g}")
out["fisher"] = tests
json.dump(out, open("results/phase4b/analysis.json", "w"), indent=1, default=float)
