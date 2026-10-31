"""Deployment H2 (registered, OSF vq5cp): do fields with an exact derivation route relay plausible corruptions less often than
other fields? Per model, from graded.json (delivered plausible runs): relay rates, crude odds ratio with Woolf 95% interval, and
two-sided Fisher exact p. Run from the repository root: python results/biomni_corrupt/h2_odds.py"""
import collections, json, math
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
            yield str(pick(r, "field")), bool(pick(r, "propag", "relay"))

GROUPINGS = {"exact = length, mass, molecular weight, heavy atoms": {"length", "mass", "molecular_weight", "heavy_atom_count"},
             "exact = the above + hydrogen-bond donors": {"length", "mass", "molecular_weight", "heavy_atom_count", "h_bond_donors"}}
out = {}
for model in ("deepseek", "flash"):
    rs = list(runs(f"results/biomni_full_{model}/graded.json"))
    for name, exact in GROUPINGS.items():
        c = collections.Counter((f in exact, p) for f, p in rs)
        a, b, cc, d = c[(True, True)], c[(True, False)], c[(False, True)], c[(False, False)]
        orr = a * d / (b * cc); se = math.sqrt(1 / a + 1 / b + 1 / cc + 1 / d)
        res = {"exact": f"{a}/{a + b} ({100 * a / (a + b):.1f}%)", "other": f"{cc}/{cc + d} ({100 * cc / (cc + d):.1f}%)",
               "odds_ratio": round(orr, 2), "ci95": [round(math.exp(math.log(orr) - 1.96 * se), 2), round(math.exp(math.log(orr) + 1.96 * se), 2)],
               "fisher_p_two_sided": float(fisher_exact([[a, b], [cc, d]])[1])}
        out.setdefault(model, {})[name] = res; print(f"{model:8s} {name:55s} {res}")
json.dump(out, open("results/biomni_corrupt/h2_odds.json", "w"), indent=1)
