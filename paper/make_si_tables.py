"""Supplementary Tables 6-13: the counts behind Figs. 1-6, computed with the figure script's own loaders.
Run from the repository root: python paper/make_si_tables.py"""
import collections, glob, json, re, sys
sys.path.insert(0, "paper")
import make_figures_nmi as mf  # same loaders as the figures (regenerates them as a side effect)
load, kn, flagged = mf.load, mf.kn, mf.flagged
NAME = {"opus5": "Opus 5", "sonnet5": "Sonnet 5", "sonnet46": "Sonnet 4.6", "haiku45": "Haiku 4.5", "argon": "Gemini 4 Argon", "gemini4argon": "Gemini 4 Argon",
        "flash": "Gemini 3.8 Flash", "gemini38flash": "Gemini 3.8 Flash", "deepseek": "DeepSeek V4.1 Flash", "deepseek_v41flash": "DeepSeek V4.1 Flash",
        "gpt61sol": "GPT-6.1 Sol", "gpt6luna": "GPT-6 Luna", "kimi_k3": "Kimi K3"}
ORDER10 = ["opus5", "gemini4argon", "deepseek_v41flash", "gpt61sol", "gpt6luna", "kimi_k3", "sonnet5", "sonnet46", "gemini38flash", "haiku45"]
M5 = ["opus5", "sonnet5", "argon", "flash", "deepseek"]; M4 = ["opus5", "argon", "flash", "deepseek"]; M3 = ["opus5", "argon", "deepseek"]
def frac(k, n): return f"{k}/{n} ({100 * k / n:.0f}\\%)" if n else "--"
def esc(s): return str(s).replace("_", " ")
out = []
def table(caption, header, rows, wide=False):
    body = "\n".join(" & ".join(r) + " \\\\" for r in rows)
    tab = f"\\begin{{tabular}}{{{'l' * len(header)}}}\n\\toprule\n{' & '.join(header)} \\\\\n\\midrule\n{body}\n\\bottomrule\n\\end{{tabular}}"
    if wide: tab = "\\resizebox{\\textwidth}{!}{" + tab + "}"
    out.append(f"\\begin{{table}}[p]\n\\centering\\small\n\\caption{{{caption}}}\n{tab}\n\\end{{table}}\n")

# Table 6: deployment rerun by field (Fig. 1b, c)
rows = []
for m in ("deepseek", "flash"):
    G = [r for r in json.load(open(f"results/biomni_rerun/{m}/graded.json")) if r["delivered"]]
    for cond in ("impossible", "plausible"):
        by = collections.defaultdict(lambda: [0, 0, 0])
        for r in G:
            if r["cond"] == cond: x = by[r["field"]]; x[1] += 1; x[0] += bool(r["propagated"]); x[2] += bool(r["propagated"] and r["flagged"])
        for f, (k, n, fl) in sorted(by.items()): rows.append([NAME[m], cond, esc(f), frac(k, n), f"{fl}/{k}" if k else "--"])
table("Deployment rerun (Fig.~1b, c): corrupted values relayed by field (relayed/delivered runs) and, among relayed runs, how many raised a concern.",
      ["Model", "Condition", "Field", "Relayed", "Flagged among relayed"], rows)

# Table 7: benchmark (Fig. 2)
def bench(path):
    return [t for t in load(path) if t.get("condition") in ("impossible", "plausible") and not t.get("verify_prompt") and (t.get("prompt_variant") or "default") == "default"
            and t.get("record_format") in (None, "summary") and t.get("harness") in (None, "none", False) and str(t.get("sample", 0)) == "0"]
rows = []; check = {}
for m in ORDER10:
    for dom, d in (("proteins", "v2"), ("molecules", "chem")):
        ts = bench(f"results/{d}/traces_{m}.jsonl")
        for cond in ("impossible", "plausible"):
            c = [t for t in ts if t["condition"] == cond]
            if not c: continue
            k, n = kn(c); fl = sum(flagged(t) for t in c); kf = sum(flagged(t) for t in c if t.get("propagated"))
            rows.append([NAME[m], dom, cond, frac(k, n), frac(fl, n), f"{kf}/{k}" if k else "--"]); check[(m, dom, cond)] = round(100 * k / n)
table("Benchmark (Extended Data Fig.~1): corrupted values relayed, runs raising a concern, and relayed runs that raised a concern (summary record, registered prompt, one sample).",
      ["Model", "Domain", "Condition", "Relayed", "Flagged", "Flagged among relayed"], rows)
print("check Fig. 2, Opus 5 proteins impossible: expect 32, got", check.get(("opus5", "proteins", "impossible")))

# Tables 8-9: boundaries (Fig. 3)
data = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for f in glob.glob("results/boundary/traces_*.jsonl"):
    mm = re.match(r".*traces_(.+)_(protein|chem)_(shrink|inflate)\.jsonl$", f)
    if not mm: continue
    for t in load(f):
        fm = re.match(r"f([\d.]+)_", str(t.get("condition", "")))
        if fm: x = data[mm.groups()][float(fm.group(1))]; x[0] += bool(t.get("propagated")); x[1] += 1
for direction, word in (("shrink", "decreased"), ("inflate", "increased")):
    keys = sorted({k for g in data if g[2] == direction for k in data[g]}, reverse=(direction == "shrink"))
    rows = []
    for m in M5:
        for dom in ("protein", "chem"):
            g = (m, dom, direction)
            if g in data: rows.append([NAME[m], "proteins" if dom == "protein" else "molecules"] + [f"{data[g][k][0]}/{data[g][k][1]}" if k in data[g] else "--" for k in keys])
    table(f"Override boundaries (Extended Data Fig.~2), value {word}: corrupted value relayed (relayed/parsed runs) at each corruption factor, full record, paired field scaled alike.",
          ["Model", "Domain"] + [f"$\\times${k:g}" for k in keys], rows, wide=True)

# Table 10: new chemistry fields (Fig. 4a)
rows = []
for m in M5:
    ts = load(f"results/phase4/{m}_full.jsonl")
    for field in sorted({str(t.get("target_field")) for t in ts}):
        for cond in ("clean", "plausible", "impossible"):
            c = [t for t in ts if str(t.get("target_field")) == field and t.get("condition") == cond]
            if c: rows.append([NAME[m], esc(field), cond, frac(sum(flagged(t) for t in c), len(c)), frac(*kn(c)) if cond != "clean" else "--"])
table("New chemistry fields with the full record (Fig.~4a): runs raising a concern and corrupted values relayed, by field and condition.",
      ["Model", "Field", "Condition", "Flagged", "Relayed"], rows)

# Table 11: agreement arms (Fig. 4b, c)
ARMS4 = [("P4", "mono.\\ mass asked, two agreeing fields"), ("A", "mono.\\ mass asked, corrupted alone"), ("B", "weight asked, one agreeing field"), ("C", "weight asked, two agreeing fields")]
rows = []
for m in M4:
    for a, lab in ARMS4:
        ts = load(f"results/robustness/{m}_4b_{a}.jsonl", "plausible")
        rows.append([NAME[m], lab, frac(*kn(ts))] + [frac(*kn([t for t in ts if str(t.get("sample", 0)) == s])) for s in ("0", "1", "2")])
table("Agreement follow-up (Fig.~4b, c): wrong value relayed on the same 60 compounds, pooled over three samples and per sample.",
      ["Model", "Arm", "Pooled", "Sample 1", "Sample 2", "Sample 3"], rows, wide=True)

# Tables 12-13: historical errors (Figs. 5, 6)
T = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
from harness import second_source as ss
cov = lambda t: bool(ss._AF.get(T[t["task_id"]]["target_accession"]))
def direction(t):
    c = t.get("corruption") or T[t["task_id"]].get("corruption") or {}
    return {"old_longer": "longer", "old_shorter": "shorter"}.get(c.get("direction"))
rows = []
for m in M3:
    ann = load(f"results/robustness/{m}_p5_annotate.jsonl", "superseded"); annc = [t for t in ann if cov(t)]
    lon = [t for t in annc if direction(t) == "longer"]; sho = [t for t in annc if direction(t) == "shorter"]
    rows.append([NAME[m], frac(*kn(load(f"results/phase5/{m}_full.jsonl", "superseded"))), frac(*kn(load(f"results/phase5/{m}_summary.jsonl", "superseded"))),
                 frac(*kn(load(f"results/robustness/{m}_p5_full.jsonl", "superseded"))), frac(*kn(annc)), frac(*kn(lon)), frac(*kn(sho)), frac(*kn([t for t in ann if not cov(t)]))])
    if m == "opus5": print("check Fig. 5c, Opus 5 longer: expect 16/63, got", kn(lon))
table("Historical UniProt errors (Fig.~2): superseded value relayed with the full and summary record (one sample), full-record repeats (three samples), and with AlphaFold DB as second source (annotate arm, three samples) on covered proteins, by direction of the revision, and on the uncovered protein.",
      ["Model", "Full record", "Summary", "Full, repeats", "Second source", "Superseded longer", "Superseded shorter", "Uncovered"], rows, wide=True)
ARMS = [("p5_annotate", "annotate: conflict listed"), ("p5_replace", "replace: ambiguous labels"), ("p5_replace_labeled", "replace: original labelled"), ("p5_replace_silent", "replace: silent")]
rows = []
for m in M3:
    for a, lab in ARMS:
        ts = [t for t in load(f"results/robustness/{m}_{a}.jsonl", "superseded") if cov(t)]
        rows.append([NAME[m], lab, frac(*kn(ts))] + [frac(*kn([t for t in ts if str(t.get("sample", 0)) == s])) for s in ("0", "1", "2")])
table("Presentation of the correction (Fig.~6): superseded value relayed on covered proteins under four presentations, pooled over three samples and per sample.",
      ["Model", "Presentation", "Pooled", "Sample 1", "Sample 2", "Sample 3"], rows)

open("paper/nmi/si_tables.tex", "w").write("\\clearpage\n\\section*{Supplementary Tables 6--13: counts behind Figures 1, 2, 4 and 6 and Extended Data Figures 1 and 2}\n\n" + "\n".join(out))
print("wrote paper/nmi/si_tables.tex with", len(out), "tables")
