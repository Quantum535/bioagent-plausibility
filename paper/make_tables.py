#!/usr/bin/env python3
"""Extra LaTeX tables for the full paper: per-condition results, impossible-mass variants, task templates."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "tables"
OUT.mkdir(exist_ok=True)
S = json.loads((ROOT / "results" / "summary.json").read_text())
tasks = {t["task_id"]: t for t in json.loads((ROOT / "data" / "tasks.json").read_text())["tasks"]}
MODELS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-sonnet-5", "claude-opus-5"]
LABEL = {"claude-haiku-4-5": "Haiku 4.5", "claude-sonnet-4-6": "Sonnet 4.6", "claude-sonnet-5": "Sonnet 5", "claude-opus-5": "Opus 5"}
CONDS = ["impossible", "plausible", "impossible+verify", "plausible+verify"]


def pct(a):
    return f"{100 * a['rate']:.0f}" if a and a["rate"] is not None else "--"


def ci(a):
    return f"[{100 * a['ci_lo']:.0f}, {100 * a['ci_hi']:.0f}]"


# ---- main results table
L = ["\\begin{tabular}{llrrrrrrr}", "\\toprule",
     "model & condition & $n$ & accuracy & propagation & 95\\% CI & flagged & silent & recall \\\\", "\\midrule"]
for m in MODELS:
    for c in CONDS:
        a = S["by_model_condition"][m].get(c)
        if not a:
            continue
        L.append(f"{LABEL[m]} & {c.replace('+verify', ' + verify')} & {a['n']} & {pct(a['accuracy'])} & {pct(a['propagation'])} & {ci(a['propagation'])} & "
                 f"{pct(a['flag_rate'])} & {pct(a['silent_propagation'])} & {pct(a['recall_rate'])} \\\\")
    if m != MODELS[-1]:
        L.append("\\addlinespace[2pt]")
L += ["\\bottomrule", "\\end{tabular}"]
(OUT / "main_results.tex").write_text("\n".join(L) + "\n")

# ---- impossible-mass variants
runs = S["runs"]
L = ["\\begin{tabular}{lcccc}", "\\toprule", " & \\multicolumn{2}{c}{baseline} & \\multicolumn{2}{c}{+verify} \\\\",
     "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}", "model & negative mass & 45 Da & negative mass & 45 Da \\\\", "\\midrule"]
for m in MODELS:
    row = [LABEL[m]]
    for cond in ("impossible", "impossible+verify"):
        sub = [r for r in runs if r["model"] == m and r["condition"] == cond and r["target_field"] == "mass"]
        for sel in (lambda v: v < 0, lambda v: v == 45):
            g = [r for r in sub if sel(tasks[r["task_id"]]["corruptions"]["impossible"]["corrupted_value"])]
            row.append(f"{sum(r['correct'] for r in g)}/{len(g)}")
    L.append(" & ".join(row) + " \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
(OUT / "mass_variants.tex").write_text("\n".join(L) + "\n")

# ---- task templates
L = ["\\begin{tabular}{lp{7.6cm}clc}", "\\toprule", "template & prompt (before the answer-field sentence) & calls & graded answer & tasks \\\\", "\\midrule",
     "length threshold & Does protein \\{acc\\} have more than \\{T\\} residues? Answer yes or no and give the count. & 1 & yes/no & 5 \\\\",
     "length ratio & Is \\{gene\\_A\\} at least twice as long as \\{gene\\_B\\}? Answer yes or no with both lengths. & 2 & yes/no & 5 \\\\",
     "mass comparison & Which is heavier, the protein encoded by \\{gene\\_A\\} or \\{gene\\_B\\}? Give the gene symbol and both masses in kDa. & 2 & gene symbol & 10 \\\\",
     "organism & What organism is \\{acc\\} from, and is it a mammal? Answer with organism and yes/no. & 1 & organism & 10 \\\\",
     "gene symbol & What gene encodes \\{acc\\}? Answer with the gene symbol. & 1 & gene symbol & 10 \\\\",
     "\\bottomrule", "\\end{tabular}"]
(OUT / "templates.tex").write_text("\n".join(L) + "\n")

# ---- corruption spec with a worked example (task t000's protein)
ex = tasks["t000"]; acc = ex["target_accession"]
L = ["\\begin{tabular}{lp{3.9cm}p{3.1cm}p{3.6cm}}", "\\toprule", "target field & impossible & plausible & severity sweep \\\\", "\\midrule",
     "length & 3 residues, mass unchanged & $\\times\\{0.75, 0.8\\}$, mass scaled alike & $\\times$0.9 \\dots\\ $\\times$0.005; mass scaled alike (consistent) or unchanged \\\\",
     "mass & 45 Da or $-$mass, length unchanged & $\\times\\{0.75, 0.8\\}$, length scaled alike & $\\times$0.9 \\dots\\ $\\times$0.005; length scaled alike (consistent) or unchanged \\\\",
     "organism & \\emph{Escherichia coli} K-12, compartment eukaryote-only & \\emph{Mus musculus} & -- \\\\",
     "gene symbol & random symbol absent from the table (e.g.\\ WDD8) & symbol of another table protein & -- \\\\",
     "\\midrule",
     f"example ({acc}) & 3 aa / 58,043 Da & 376 aa / 43,532 Da & 452 aa / 52,239 Da at $\\times$0.9, consistent \\\\",
     "\\bottomrule", "\\end{tabular}"]
(OUT / "corruptions.tex").write_text("\n".join(L) + "\n")
print("tables written:", sorted(p.name for p in OUT.iterdir()))
