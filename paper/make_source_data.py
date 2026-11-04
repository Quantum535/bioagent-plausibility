"""Source Data: one CSV per main and Extended Data figure, assembled from the Supplementary Tables and the run files. Run from the repository root."""
import csv, glob, json, os, re, sys, collections
OUT = "paper/nmi/source_data"; os.makedirs(OUT, exist_ok=True)
def clean(x):
    x = x.replace("\\%", "%").replace("\\_", "_").replace("\\&", "&").replace("$\\times$", "x").replace("$<10^{-10}$", "<1e-10").replace("\\\\", "").replace("--", "-")
    x = re.sub(r"\$([^$]*)\$", r"\1", x); x = re.sub(r"\\(textbf|emph|path|texttt)\{([^}]*)\}", r"\2", x); x = re.sub(r"\\times 10\^\{([^}]*)\}", r"e\1", x)
    return x.replace("{", "").replace("}", "").replace("~", " ").strip()
tables = []
for f in ("paper/nmi/supplement.tex", "paper/nmi/si_tables.tex", "paper/nmi/si_round2.tex"):
    for b in re.findall(r"\\begin\{table\}.*?\\end\{table\}", open(f).read(), flags=re.S):
        cap = clean(re.search(r"\\caption\{(.*?)\}\n", b, flags=re.S).group(1)) if "\\caption{" in b else ""
        head = re.search(r"\\toprule\s*(.*?)\\\\\s*\\midrule", b, flags=re.S).group(1); body = re.search(r"\\midrule\s*(.*?)\\bottomrule", b, flags=re.S).group(1)
        rows = [[clean(c) for c in head.split(" & ")]] + [[clean(c) for c in l.split(" & ")] for l in body.strip().split("\n") if " & " in l]
        tables.append((cap, rows))
for i, (cap, rows) in enumerate(tables, 1):
    with open(f"{OUT}/Supplementary_Table_{i}.csv", "w", newline="") as fh: w = csv.writer(fh); w.writerow([f"Supplementary Table {i}. {cap}"]); w.writerows(rows)
print(len(tables), "supplementary tables exported")
def extra_fig3d():
    G = {(r["task"], r["cond"]): r for r in json.load(open("results/biomni_rerun/flash/graded.json"))}; comp = {}
    LEN = re.compile(r"len\(\s*[\w\.\[\]'\"]*seq|ProteinAnalysis|molecular_weight\(|calculate.{0,20}(mass|weight)|count.{0,20}residue", re.I)
    for f in glob.glob("results/biomni_rerun/flash/out_*.json"):
        o = json.load(open(f)); t = o.get("final") or ""
        comp[(str(o.get("task_id")), str(o.get("condition")))] = bool(LEN.search(" ".join(re.findall(r"<execute>(.*?)(?=<execute>|<observ|<solution>|$)", t, flags=re.S))))
    rows = [["panel d: field", "computed from sequence", "relayed", "delivered plausible runs"]]
    for fld in ("length", "mass"):
        D = [r for r in G.values() if r["cond"] == "plausible" and r["delivered"] and r["parsed"] and r["field"] == fld]
        for c in (True, False):
            x = [r for r in D if comp.get((r["task"], "plausible"), False) == c]; rows.append([fld, c, sum(bool(r["propagated"]) for r in x), len(x)])
    return rows
def extra_fig6b():
    try:
        sys.path.insert(0, "paper"); import make_figures_nmi as mf
        from harness import second_source as ss
        T = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}; cov = lambda t: bool(ss._AF.get(T[t["task_id"]]["target_accession"]))
        rows = [["panel b: model", "presentation", "what the relayed answer cited", "runs"]]
        for m in ("opus5", "argon", "deepseek"):
            for a in ("p5_annotate", "p5_replace", "p5_replace_labeled"):
                c = collections.Counter(mf.reason(t) for t in mf.load(f"results/robustness/{m}_{a}.jsonl", "superseded") if cov(t) and t.get("propagated"))
                rows += [[m, a, k, v] for k, v in sorted(c.items())]
        return rows
    except Exception as e:
        return [["panel b could not be regenerated here (" + type(e).__name__ + "); see paper/make_figures_nmi.py, function fig6"]]
FIGS = {"Fig1": ([1, 6], None), "Fig2": ([12, 19], None), "Fig3": ([14, 15, 17], extra_fig3d), "Fig4": ([10, 11], None), "Fig5": ([2, 3, 18, 4, 5], None), "Fig6": ([13], extra_fig6b),
        "Extended_Data_Fig1": ([7], None), "Extended_Data_Fig2": ([8, 9], None)}
for name, (idx, extra) in FIGS.items():
    with open(f"{OUT}/Source_Data_{name}.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow([f"Source Data {name.replace('_', ' ')}. Counts are relayed (or correct) runs over runs with a parseable answer; rates and 95% Wilson intervals in the figure are computed from them by the figure scripts in paper/."])
        for i in idx: cap, rows = tables[i - 1]; w.writerow([]); w.writerow([f"Supplementary Table {i}. {cap}"]); w.writerows(rows)
        if extra: w.writerow([]); w.writerows(extra())
    print("wrote", f"{OUT}/Source_Data_{name}.csv")
