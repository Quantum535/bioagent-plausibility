"""Round 2 analysis (registration: results/round2/PREREGISTRATION.md). Run from the repository root."""
import json, glob, os, re, random
from scipy.stats import binomtest
R = "results/round2"
BENCH = {"opus5": "opus5", "argon": "gemini4argon", "deepseek": "deepseek_v41flash", "sonnet5": "sonnet5", "flash": "gemini38flash"}
OUT = {}
def rows(path, errors=False):
    if not os.path.exists(path): return []
    d = {}
    for i, l in enumerate(open(path)):
        try: r = json.loads(l)
        except Exception: continue
        d[r.get("run_key", i)] = r
    return list(d.values()) if errors else [r for r in d.values() if not (r.get("trace") or {}).get("error")]
def parsed(r): return (r.get("trace") or {}).get("parsed_ok", True)
def default(r): return (r.get("prompt_variant") or "default") == "default" and not r.get("verify_prompt") and r.get("harness") in (None, "none", False)
def s0(r): return str(r.get("sample", 0)) == "0"
def cnt(rs, cond, what="propagated"):
    c = [r for r in rs if r.get("condition") == cond]; p = [r for r in c if parsed(r)]
    return sum(bool(r.get(what)) for r in p), len(p), len(c) - len(p)
def fmt(k, n, u=0, relay=True):
    if not n: return "--"
    s = f"{k}/{n} ({100 * k / n:.0f}%)"
    if u: s += f" [+{u} unparsed; {'if relayed' if relay else 'as failures'} {(k + u if relay else k)}/{n + u}]"
    return s
def paired(a, b, key, alt="two-sided"):  # a = baseline, b = variant; alt "greater": variant relays more
    A = {key(r): bool(r.get("propagated")) for r in a if parsed(r)}; B = {key(r): bool(r.get("propagated")) for r in b if parsed(r)}
    ks = [k for k in A if k in B]; up = sum(B[k] and not A[k] for k in ks); down = sum(A[k] and not B[k] for k in ks)
    p = binomtest(up, up + down, 0.5, alternative=alt).pvalue if up + down else 1.0
    return {"pairs": len(ks), "base": sum(A[k] for k in ks), "variant": sum(B[k] for k in ks), "up": up, "down": down, "p": p}
def ptxt(d): return f"paired n={d['pairs']}: {d['base']} -> {d['variant']} relayed ({d['up']} up, {d['down']} down), p={d['p']:.2g}"

print("=== COMPLETENESS (unique successful runs / target; errors)")
T = {"IS_hist": 79, "IS_bench": 225, "NC_protein": 200, "NC_chem": 200, "F1": 120, "F2": 60, "TH_full": 100, "TH_protein": 400, "TH_chem": 200}
for f in sorted(glob.glob(f"{R}/*.jsonl")):
    allr = rows(f, errors=True); ok = rows(f); t = next(v for k, v in T.items() if f.endswith(k + ".jsonl"))
    keys_ok = {r["run_key"] for r in ok}; err = sum(1 for r in allr if r["run_key"] not in keys_ok)
    print(f"  {os.path.basename(f):26s} {len(ok):4d}/{t}" + (f"  errors {err}" if err else "") + ("" if len(ok) >= t else "  INCOMPLETE"))

print("\n=== IS: identity-stripped records")
for m in ("opus5", "argon", "deepseek"):
    h = rows(f"{R}/{m}_IS_hist.jsonl"); hb = [r for r in rows(f"results/phase5/{m}_full.jsonl") if r.get("condition") == "superseded"]
    print(f"  {m:8s} IS1 historical, no identity: {fmt(*cnt(h, 'superseded'))}   with identity (full record): {fmt(*cnt(hb, 'superseded'))}")
    b = rows(f"{R}/{m}_IS_bench.jsonl"); tasks = {r["task_id"] for r in b}
    base = [r for r in rows(f"results/v2_full/traces_{BENCH[m]}.jsonl") if default(r) and r["task_id"] in tasks]
    for cond in ("plausible", "impossible"):
        d = paired(base, [r for r in b if s0(r)], lambda r: (r["task_id"], r["condition"]) if r.get("condition") == cond else None)
        d = paired([r for r in base if r.get("condition") == cond], [r for r in b if s0(r) and r.get("condition") == cond], lambda r: r["task_id"])
        print(f"           {cond:10s} no identity, 3 samples: {fmt(*cnt(b, cond))}   with identity: {fmt(*cnt(base, cond))}   sample 1 vs identity {ptxt(d)}")
        OUT.setdefault("IS", {})[f"{m}_{cond}"] = {"no_identity": cnt(b, cond), "identity": cnt(base, cond), "paired": d}
    print(f"           clean accuracy, no identity: {fmt(*cnt(b, 'clean', 'correct'), relay=False)}")
    OUT["IS"][f"{m}_hist"] = {"no_identity": cnt(h, "superseded"), "identity": cnt(hb, "superseded")}; OUT["IS"][f"{m}_clean"] = cnt(b, "clean", "correct")

print("\n=== NC: prompt without the concerns field (summary record, first 100 tasks per domain)")
KW = re.compile(r"inconsisten|discrepan|mismatch|suspicious|implausible|incorrect|erroneous|wrong|surprising|does(?: not|n't) match|can(?:not|'t) be|unusual", re.I)
def text(r):
    t = (r.get("trace") or {}).get("final_text") or ""; return t[:t.rfind("{")] if "{" in t else t
def kw(r): return bool(KW.search(text(r)))
def solicited(r): return bool((r.get("trace") or {}).get("concerns"))
sample_pool = []
for m in ("opus5", "argon", "deepseek"):
    for dom, bpath in (("protein", f"results/v2/traces_{BENCH[m]}.jsonl"), ("chem", f"results/chem/traces_{BENCH[m]}.jsonl")):
        nc = rows(f"{R}/{m}_NC_{dom}.jsonl"); tasks = {r["task_id"] for r in nc}
        base = [r for r in rows(bpath) if default(r) and s0(r) and r.get("record_format") in (None, "summary") and r["task_id"] in tasks]
        for cond in ("impossible", "plausible"):
            n_, b_ = [r for r in nc if r.get("condition") == cond and parsed(r)], [r for r in base if r.get("condition") == cond and parsed(r)]
            d = paired(b_, n_, lambda r: r["task_id"])
            fl = lambda rs, f: f"{sum(map(f, rs))}/{len(rs)} ({100 * sum(map(f, rs)) / max(len(rs), 1):.0f}%)"
            print(f"  {m:8s} {dom:7s} {cond:10s} relay default {fmt(*cnt(base, cond))}  no concerns {fmt(*cnt(nc, cond))}  {ptxt(d)}")
            print(f"  {'':8s} {'':7s} {'':10s} flags: solicited (default) {fl(b_, solicited)}; keyword in default text {fl(b_, kw)}; keyword without the field {fl(n_, kw)}")
            OUT.setdefault("NC", {})[f"{m}_{dom}_{cond}"] = {"default": cnt(base, cond), "no_concerns": cnt(nc, cond), "paired": d,
                "solicited": [sum(map(solicited, b_)), len(b_)], "kw_default": [sum(map(kw, b_)), len(b_)], "kw_nc": [sum(map(kw, n_)), len(n_)]}
            sample_pool += [(m, dom, cond, r) for r in n_]
random.seed(7); smp = random.sample(sample_pool, min(50, len(sample_pool)))
with open(f"{R}/nc_flag_sample.txt", "w") as fh:
    for m, dom, cond, r in smp:
        fh.write(f"### {m} {dom} {cond} {r['task_id']}  detector={'FLAG' if kw(r) else 'none'}  your label: \n{text(r)[-700:].strip()}\n\n")

print("\n=== FD: familiar duplicate field (average_mass), sample 1 of R0/R1/R2 for pairing")
acc = lambda r: r["target_accession"]; pool = {k: [] for k in ("R0", "R1", "R2", "F1", "F2")}
for m in ("opus5", "argon", "flash", "deepseek"):
    A = {a: [r for r in rows(f"results/repetition/{m}_{a}.jsonl") if s0(r) and r.get("condition") == "plausible"] for a in ("R0", "R1", "R2")}
    for a in ("F1", "F2"): A[a] = [r for r in rows(f"{R}/{m}_{a}.jsonl") if r.get("condition") == "plausible"]
    for k, v in A.items(): pool[k] += [dict(r, _m=m) for r in v]
    print(f"  {m:8s} " + "  ".join(f"{k} {fmt(*cnt(v, 'plausible'))}" for k, v in A.items()) + f"  F1 clean accuracy {fmt(*cnt(rows(f'{R}/{m}_F1.jsonl'), 'clean', 'correct'), relay=False)}")
    print(f"           FD1 F1 vs R1 {ptxt(paired(A['R1'], A['F1'], acc, 'greater'))};  FD3 F2 vs R0 {ptxt(paired(A['R0'], A['F2'], acc, 'less'))}")
pk = lambda r: (r["_m"], r["target_accession"])
for name, (a, b, alt) in {"FD1 F1>R1": ("R1", "F1", "greater"), "FD2 F1 vs R0": ("R0", "F1", "two-sided"), "FD3 F2<R0": ("R0", "F2", "less")}.items():
    d = paired(pool[a], pool[b], pk, alt); OUT.setdefault("FD", {})[name] = d; print(f"  pooled {name}: {ptxt(d)}")

print("\n=== TH: thinking disabled")
th = rows(f"{R}/opus5_TH_full.jsonl"); tasks = {r["task_id"] for r in th}
print(f"  thinking field in TH runs: {sorted({str(r.get('thinking')) for r in th})}")
base = [r for r in rows("results/v2_full/traces_opus5.jsonl") if default(r) and r["task_id"] in tasks]
for cond in ("impossible", "plausible"):
    d = paired([r for r in base if r.get("condition") == cond], [r for r in th if r.get("condition") == cond], lambda r: r["task_id"], "greater")
    print(f"  Opus 5 full record {cond:10s} adaptive {fmt(*cnt(base, cond))}  disabled {fmt(*cnt(th, cond))}  TH1 {ptxt(d)}"); OUT.setdefault("TH", {})[f"opus5_full_{cond}"] = d
for dom, bpath in (("protein", "results/v2/traces_sonnet5.jsonl"), ("chem", "results/chem/traces_sonnet5.jsonl")):
    th = rows(f"{R}/sonnet5_TH_{dom}.jsonl"); tasks = {r["task_id"] for r in th}
    base = [r for r in rows(bpath) if default(r) and s0(r) and r.get("record_format") in (None, "summary") and r["task_id"] in tasks]
    for cond, alt in (("impossible", "greater"), ("plausible", "two-sided")):
        d = paired([r for r in base if r.get("condition") == cond], [r for r in th if r.get("condition") == cond], lambda r: r["task_id"], alt)
        print(f"  Sonnet 5 {dom:7s} {cond:10s} adaptive {fmt(*cnt(base, cond))}  disabled {fmt(*cnt(th, cond))}  {'TH1' if alt == 'greater' else 'TH2'} {ptxt(d)}")
        OUT["TH"][f"sonnet5_{dom}_{cond}"] = d
json.dump(OUT, open(f"{R}/analysis.json", "w"), indent=1, default=str); print("\nwrote results/round2/analysis.json and results/round2/nc_flag_sample.txt")
