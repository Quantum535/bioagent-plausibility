"""Phase 4 confirmatory analysis exactly as pre-registered (results/phase4/PREREGISTRATION.md), plus descriptive tables.
Exclusions: API-errored runs; runs with no parseable answer; model x field x format cells with clean accuracy < 80%."""
import json, collections
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import fisher_exact, norm
R = "results/phase4"; MODELS = ["opus5", "sonnet5", "argon", "flash", "deepseek"]; H1M = ["opus5", "argon", "flash", "deepseek"]
RANK = {"monoisotopic_mass": 0, "tpsa": 1, "complexity": 2}
direction = {t["task_id"]: t["direction"] for t in json.load(open("data/chem/phase4_tasks.json"))["tasks"]}
rows, excl = [], collections.Counter()
for m in MODELS:
    for fmt in ("full", "summary"):
        seen = {}
        for l in open(f"{R}/{m}_{fmt}.jsonl"):
            t = json.loads(l); seen[t["run_key"]] = t
        for t in seen.values():
            tr = t.get("trace") or {}
            if tr.get("error"): excl[f"{m}/{fmt}/api_error"] += 1; continue
            if not tr.get("parsed_ok", True): excl[f"{m}/{fmt}/unparsed"] += 1; continue
            rows.append({"model": m, "format": fmt, "field": t["target_field"], "rank": RANK[t["target_field"]], "direction": direction[t["task_id"]],
                         "condition": t["condition"], "correct": int(bool(t.get("correct"))), "prop": int(bool(t.get("propagated"))),
                         "flag": int(bool(tr.get("concerns"))), "full": int(fmt == "full")})
df = pd.DataFrame(rows); out = {"excluded_runs": dict(excl)}
print("excluded runs:", dict(excl) or "none")
ca = df[df.condition == "clean"].groupby(["model", "field", "format"]).correct.mean()
bad = set(ca[ca < 0.8].index); out["clean_acc_min"] = float(ca.min()); out["cells_excluded"] = [list(b) for b in sorted(bad)]
print(f"clean accuracy: min {ca.min():.2f}; cells < 80% excluded from H1-H3: {sorted(bad) or 'none'}")
keep = df[~df.set_index(["model", "field", "format"]).index.isin(bad)]
for cond in ("plausible", "impossible"):
    print(f"\n{cond} propagation k/n{'  (exploratory)' if cond == 'impossible' else ''}:  model  format | mono | TPSA | complexity")
    for m in MODELS:
        for fmt in ("full", "summary"):
            cells = []
            for fld in RANK:
                g = keep[(keep.condition == cond) & (keep.model == m) & (keep.format == fmt) & (keep.field == fld)]
                cells.append(f"{g.prop.sum()}/{len(g)}"); out[f"{cond}|{m}|{fmt}|{fld}"] = [int(g.prop.sum()), int(len(g))]
            print(f"  {m:9s} {fmt:8s} | " + " | ".join(cells))
pl = keep[keep.condition == "plausible"]
d1 = pl[(pl.full == 1) & pl.model.isin(H1M)]
print("\nH1 primary: logit prop ~ rank + model + direction (full record, plausible, Opus/Argon/Flash/DeepSeek)")
try:
    f1 = smf.logit("prop ~ rank + C(model) + C(direction)", data=d1).fit(disp=0)
    b1, s1 = f1.params["rank"], f1.bse["rank"]; p1 = norm.sf(b1 / s1)
    print(f"  rank coefficient {b1:.3f} (SE {s1:.3f}), one-sided p = {p1:.2e} -> {'SUPPORTED' if p1 < 0.05 else 'NOT SUPPORTED'}")
    out["H1"] = {"coef": b1, "se": s1, "p_one_sided": p1}
except Exception as e:
    print("  fit failed:", e); out["H1"] = {"error": str(e)}
tests = []
for m in H1M:
    g = d1[d1.model == m]
    for a, b in (("monoisotopic_mass", "tpsa"), ("tpsa", "complexity")):
        x, y = g[g.field == a].prop, g[g.field == b].prop
        _, p = fisher_exact([[int(x.sum()), len(x) - int(x.sum())], [int(y.sum()), len(y) - int(y.sum())]], alternative="less")
        tests.append([m, a, b, int(x.sum()), len(x), int(y.sum()), len(y), p])
order = sorted(range(len(tests)), key=lambda i: tests[i][-1]); run = 0
for r, i in enumerate(order):
    run = max(run, min(1.0, (len(tests) - r) * tests[i][-1])); tests[i].append(run)
print("H1 secondary: per-model Fisher (one-sided), Holm-adjusted across 8")
for m, a, b, k1, n1, k2, n2, p, ph in tests:
    print(f"  {m:9s} {a} {k1}/{n1} < {b} {k2}/{n2}: p {p:.3g}, Holm {ph:.3g}")
out["H1_fisher"] = tests
pred = json.load(open(f"{R}/predictions_mono.json")); passes = 0
print("\nH2: monoisotopic mass, full record, plausible vs Phase 1 prediction interval")
for m in MODELS:
    for d in ("shrink", "inflate"):
        g = pl[(pl.full == 1) & (pl.model == m) & (pl.field == "monoisotopic_mass") & (pl.direction == d)]
        p, lo, hi = pred[f"{m}|{d}"]; obs = g.prop.mean() if len(g) else float("nan"); ok = bool(lo <= obs <= hi); passes += ok
        print(f"  {m:9s} {d:8s} predicted {100 * p:.0f}% [{100 * lo:.0f}, {100 * hi:.0f}]  observed {int(g.prop.sum())}/{len(g)} = {100 * obs:.0f}%  {'inside' if ok else 'OUTSIDE'}")
        out[f"H2|{m}|{d}"] = {"pred": [p, lo, hi], "obs": [int(g.prop.sum()), int(len(g))], "inside": ok}
print(f"  {passes}/10 inside -> {'SUPPORTED' if passes >= 8 else 'NOT SUPPORTED'}"); out["H2_passes"] = passes
d3 = pl[pl.model.isin(H1M)]
print("\nH3: logit prop ~ rank * full + model + direction (plausible, both formats)")
try:
    f3 = smf.logit("prop ~ rank * full + C(model) + C(direction)", data=d3).fit(disp=0)
    b3, s3 = f3.params["rank:full"], f3.bse["rank:full"]; p3 = norm.sf(b3 / s3)
    print(f"  rank x full coefficient {b3:.3f} (SE {s3:.3f}), one-sided p = {p3:.2e} -> {'SUPPORTED' if p3 < 0.05 else 'NOT SUPPORTED'}")
    out["H3"] = {"coef": b3, "se": s3, "p_one_sided": p3}
except Exception as e:
    print("  fit failed:", e); out["H3"] = {"error": str(e)}
fp = pl[pl.full == 1].groupby(["model", "field"]).apply(lambda g: f"{int((g.flag & g.prop).sum())}/{int(g.prop.sum())}")
print("\nExploratory: flagged among propagated, full record plausible (model, field):"); print(fp.to_string())
json.dump(out, open(f"{R}/analysis.json", "w"), indent=1, default=float)
