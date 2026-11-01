"""Deployment H2 (OSF jmwab): do fields with an exact derivation route relay plausible corruptions less often than other fields?
Registered test: logistic regression of relay on route class with task-clustered standard errors. Crude odds ratios with Woolf
intervals and Fisher exact p are given for reference. Run from the repository root: python results/biomni_corrupt/h2_odds.py"""
import collections, json, math
import numpy as np, statsmodels.api as sm
from scipy.stats import fisher_exact

def runs(path):
    def walk(x, ctx):
        if isinstance(x, dict):
            ks = [str(k).lower() for k in x]
            if any("propag" in k or "relay" in k for k in ks) and any("field" in k for k in ks):
                yield {**ctx, **x}; return
            for k, v in x.items():
                yield from walk(v, {**ctx, "condition": str(k).lower()} if str(k).lower() in ("clean", "impossible", "plausible") else ctx)
        elif isinstance(x, list):
            for v in x: yield from walk(v, ctx)
    pick = lambda r, *subs: next((v for k, v in r.items() if any(sb in str(k).lower() for sb in subs)), None)
    for r in walk(json.load(open(path)), {}):
        if "plausible" in str(pick(r, "cond") or "").lower() and pick(r, "deliver") is not False and pick(r, "propag", "relay") is not None:
            yield str(pick(r, "field")), bool(pick(r, "propag", "relay")), str(pick(r, "task"))

GROUPINGS = {"registered": {"length", "mass", "molecular_weight", "heavy_atom_count"},
             "donors_as_exact": {"length", "mass", "molecular_weight", "heavy_atom_count", "h_bond_donors"}}
out = {}
for model in ("deepseek", "flash"):
    rs = list(runs(f"results/biomni_full_{model}/graded.json"))
    for name, exact in GROUPINGS.items():
        c = collections.Counter((f in exact, p) for f, p, _ in rs)
        a, b, cc, d = c[(True, True)], c[(True, False)], c[(False, True)], c[(False, False)]
        se = math.sqrt(1 / a + 1 / b + 1 / cc + 1 / d); orr = a * d / (b * cc)
        X = sm.add_constant(np.array([float(f in exact) for f, _, _ in rs])); y = np.array([float(p) for _, p, _ in rs])
        groups = np.unique([t for _, _, t in rs], return_inverse=True)[1]
        fit = sm.GLM(y, X, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": groups})
        res = {"exact": f"{a}/{a + b} ({100 * a / (a + b):.1f}%)", "other": f"{cc}/{cc + d} ({100 * cc / (cc + d):.1f}%)",
               "odds_ratio": round(math.exp(fit.params[1]), 2), "ci95_cluster": [round(math.exp(v), 2) for v in fit.conf_int()[1]],
               "p_cluster_two_sided": float(fit.pvalues[1]), "n_tasks": int(groups.max() + 1),
               "ci95_woolf": [round(math.exp(math.log(orr) - 1.96 * se), 2), round(math.exp(math.log(orr) + 1.96 * se), 2)],
               "fisher_p_two_sided": float(fisher_exact([[a, b], [cc, d]])[1])}
        out.setdefault(model, {})[name] = res; print(f"{model:8s} {name:16s} {res}")
json.dump(out, open("results/biomni_corrupt/h2_odds.json", "w"), indent=1)
