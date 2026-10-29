"""Phase 3 summary table: coherent-corruption propagation by model x condition x arm, Wilson 95% CIs.
Errored and undelivered runs are excluded and counted. Writes results/coherent/phase3_table.json."""
import json, math, os
R = "results/coherent"
ARMS = [("Full record", R), ("Summary", f"{R}/summary_noharness"), ("Harness, all-clear", f"{R}/harness_ss0"), ("Harness + 2nd source", f"{R}/harness_ss1")]
ROWS = [("Protein impossible (3 aa)", ["prot_shrink"], "coherent_impossible"),
        ("Protein plausible, shrink", ["prot_shrink"], "coherent_plausible"),
        ("Protein plausible, inflate v1 (repeat)", ["prot_inflate"], "coherent_plausible"),
        ("Protein plausible, inflate v2", ["prot_inflate_v2"], "coherent_plausible"),
        ("Chemistry impossible (methane)", ["chem_shrink"], "coherent_impossible"),
        ("Chemistry plausible", ["chem_shrink", "chem_inflate"], "coherent_plausible")]
def wilson(k, n, z=1.96):
    if n == 0: return float("nan"), float("nan")
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h
def cell(d, m, files, cond):
    rows = {}
    for f in files:
        p = f"{d}/{m}_{f}.jsonl"
        if not os.path.exists(p): continue
        for l in open(p):
            t = json.loads(l)
            if t["condition"] == cond: rows[t["run_key"]] = t
    ok = [t for t in rows.values() if not (t.get("trace") or {}).get("error")]
    return sum(bool(t.get("propagated")) for t in ok), len(ok), len(rows) - len(ok)
out = {}
for m, label in (("opus5", "Opus 5"), ("argon", "Gemini 4 Argon"), ("deepseek", "DeepSeek V4.1 Flash")):
    print(f"\n### {label}\n| Condition | " + " | ".join(a for a, _ in ARMS) + " |\n|---|" + "---|" * len(ARMS))
    for name, files, cond in ROWS:
        cells = []
        for arm, d in ARMS:
            k, n, ex = cell(d, m, files, cond); lo, hi = wilson(k, n)
            out[f"{m}|{name}|{arm}"] = {"k": k, "n": n, "excluded": ex, "ci": [lo, hi]}
            cells.append("—" if n == 0 else f"{k}/{n} ({100 * k / n:.0f}%, {100 * lo:.0f}–{100 * hi:.0f})" + (f" [{ex} excl]" if ex else ""))
        print(f"| {name} | " + " | ".join(cells) + " |")
json.dump(out, open(f"{R}/phase3_table.json", "w"), indent=1)
