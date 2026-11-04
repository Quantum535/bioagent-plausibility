"""Prompt ablation, repetition arms, blank harness: relay per cell with paired exact McNemar tests against the registered baselines."""
import collections, glob, json, re
from scipy.stats import binomtest
def load(path, conds):
    seen = {}
    try:
        for i, l in enumerate(open(path)):
            t = json.loads(l); seen[t.get("run_key", i)] = t
    except FileNotFoundError: return []
    return [t for t in seen.values() if t.get("condition") in conds and not (t.get("trace") or {}).get("error") and (t.get("trace") or {}).get("parsed_ok", True)]
def rate(rs): return (sum(bool(t.get("propagated")) for t in rs), len(rs))
def mcnemar(base, var, key, alternative="two-sided"):
    b = {key(t): bool(t.get("propagated")) for t in base}; v = {key(t): bool(t.get("propagated")) for t in var}
    pairs = [(b[k], v[k]) for k in b if k in v]; d1 = sum(1 for x, y in pairs if x and not y); d2 = sum(1 for x, y in pairs if y and not x)
    p = binomtest(d1, d1 + d2, 0.5, alternative="greater" if alternative == "less" else alternative).pvalue if d1 + d2 else float("nan")
    return len(pairs), d1, d2, p
def fmt(k, n): return f"{k}/{n} ({100*k/n:.0f}%)" if n else "0/0"
BASE_PROT = {"opus5": "results/v2_full/traces_opus5.jsonl", "argon": "results/v2_full/traces_gemini4argon.jsonl", "deepseek": "results/v2_full/traces_deepseek_v41flash.jsonl"}
NUM = {"length", "mass"}; out = {}
print("=== PROMPT ABLATION (relay; paired McNemar vs default)")
for m in ("opus5", "argon", "deepseek", "flash"):
    cells = {}
    if m in BASE_PROT:
        cells["protein, sequence contradicts value"] = ([t for t in load(BASE_PROT[m], {"plausible"}) if t.get("target_field") in NUM], lambda V: [t for t in load(f"results/prompt_ablation/{m}_protein_{V}.jsonl", {"plausible"}) if t.get("target_field") in NUM], lambda t: t["task_id"])
        cells["coherent, nothing contradicts"] = (load(f"results/coherent/{m}_prot_shrink.jsonl", {"coherent_plausible"}), lambda V: load(f"results/prompt_ablation/{m}_coherent_{V}.jsonl", {"coherent_plausible"}), lambda t: t["task_id"])
    cells["agreement C, 3 samples"] = (load(f"results/robustness/{m}_4b_C.jsonl", {"plausible"}), lambda V: load(f"results/prompt_ablation/{m}_agreeC_{V}.jsonl", {"plausible"}), lambda t: (t["task_id"], t.get("sample", 0)))
    for cell, (base, getv, key) in cells.items():
        line = f"  {m:8s} {cell:34s} default {fmt(*rate(base)):14s}"
        for V in ("no_tool_instruction", "record_errors", "two_fields"):
            var = getv(V); n, d1, d2, p = mcnemar(base, var, key); line += f" | {V[:9]} {fmt(*rate(var)):13s} p={p:.2g}"
            out[f"{m}|{cell}|{V}"] = {"base": rate(base), "variant": rate(var), "pairs": n, "p": p}
            if V == "two_fields" and var:
                hit = tot = 0
                for t in var:
                    raw = (t.get("trace") or {}).get("final_json_raw") or ""
                    try: dv = json.loads(raw).get("database_value")
                    except Exception: dv = None
                    cv = (t.get("corruption") or {}).get("corrupted_value")
                    if dv is None or cv is None: continue
                    tot += 1
                    try: hit += abs(float(dv) - float(cv)) <= 0.05 * abs(float(cv))
                    except (TypeError, ValueError): hit += str(dv).strip().lower() == str(cv).strip().lower()
                line += f" [database_value = record {fmt(hit, tot)}]"
        print(line)
print("\n=== REPETITION vs CONSISTENCY (weight asked, 3 samples; pairs by compound and sample)")
pooled = collections.defaultdict(list); acc = lambda t: (t["target_accession"], t.get("sample", 0))
for m in ("opus5", "argon", "flash", "deepseek"):
    arms = {"R0 alone": load(f"results/repetition/{m}_R0.jsonl", {"plausible"}), "R1 repeat agrees": load(f"results/repetition/{m}_R1.jsonl", {"plausible"}),
            "R2 repeat disagrees": load(f"results/repetition/{m}_R2.jsonl", {"plausible"}), "B derived agrees": load(f"results/robustness/{m}_4b_B.jsonl", {"plausible"})}
    for k, v in arms.items(): pooled[k] += v
    r = {k: fmt(*rate(v)) for k, v in arms.items()}
    c1 = mcnemar(arms["R0 alone"], arms["R1 repeat agrees"], acc, "less"); c2 = mcnemar(arms["R1 repeat agrees"], arms["B derived agrees"], acc, "less"); c3 = mcnemar(arms["R0 alone"], arms["R2 repeat disagrees"], acc, "greater")
    print(f"  {m:8s} " + "  ".join(f"{k}: {v}" for k, v in r.items()) + f"   RC1 R1>R0 p={c1[3]:.2g}  RC2 B>R1 p={c2[3]:.2g}  RC3 R2<R0 p={c3[3]:.2g}")
    cl = load(f"results/repetition/{m}_R1_clean.jsonl", {"clean"}); print(f"           R1 clean accuracy {fmt(sum(bool(t.get('correct')) for t in cl), len(cl))}")
r = {k: rate(v) for k, v in pooled.items()}; print("  pooled   " + "  ".join(f"{k}: {fmt(*v)}" for k, v in r.items()))
c1 = mcnemar(pooled["R0 alone"], pooled["R1 repeat agrees"], lambda t: (t["model"], t["target_accession"], t.get("sample", 0)), "less")
c2 = mcnemar(pooled["R1 repeat agrees"], pooled["B derived agrees"], lambda t: (t["model"], t["target_accession"], t.get("sample", 0)), "less")
c3 = mcnemar(pooled["R0 alone"], pooled["R2 repeat disagrees"], lambda t: (t["model"], t["target_accession"], t.get("sample", 0)), "greater")
print(f"  pooled   RC1 p={c1[3]:.2g} ({c1[1]} vs {c1[2]} discordant)  RC2 p={c2[3]:.2g}  RC3 p={c3[3]:.2g}  | B minus R1 = {100*(r['B derived agrees'][0]/r['B derived agrees'][1] - r['R1 repeat agrees'][0]/r['R1 repeat agrees'][1]):+.0f} points")
print("\n=== BLANK HARNESS (full record, field withheld when the derivation check fails)")
IDENT = {"gene_symbol", "organism", "name"}
for m in ("opus5", "argon", "deepseek"):
    for dom in ("protein", "chem"):
        rs = load(f"results/blank_harness/{m}_{dom}.jsonl", {"impossible", "plausible"})
        for cond in ("impossible", "plausible"):
            num = [t for t in rs if t["condition"] == cond and t.get("target_field") not in IDENT]; idn = [t for t in rs if t["condition"] == cond and t.get("target_field") in IDENT]
            print(f"  {m:8s} {dom:8s} {cond:10s} numeric fields relayed {fmt(*rate(num)):13s} identifiers relayed {fmt(*rate(idn))}")
json.dump(out, open("results/analysis/new_experiments.json", "w"), indent=1, default=str)
