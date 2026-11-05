#!/usr/bin/env python3
"""ICML figures and tables, computed from the deduplicated traces via analysis.score/classify."""
import glob, json, math, re, sys
from collections import defaultdict
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Patch, FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis import load_runs, score, classify  # noqa: E402
import matplotlib as _mpl; _mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"]})

OUT = ROOT / "paper" / "figures"; TAB = ROOT / "paper" / "tables"
OUT.mkdir(exist_ok=True); TAB.mkdir(exist_ok=True)
TW, CW = 6.75, 3.25

ORDER = ["opus-5", "gemini-4-argon", "deepseek-v4.1-flash-1017", "gpt-6.1-sol", "gpt-6-luna",
         "kimi-k3", "sonnet-5", "sonnet-4-6", "gemini-3.8-flash", "haiku-4-5"]
LABEL = {"opus-5": "Opus 5", "gemini-4-argon": "Gemini 4 Argon", "deepseek-v4.1-flash-1017": "DeepSeek V4.1 Flash",
         "gpt-6.1-sol": "GPT-6.1 Sol", "gpt-6-luna": "GPT-6 Luna", "kimi-k3": "Kimi K3", "sonnet-5": "Sonnet 5",
         "sonnet-4-6": "Sonnet 4.6", "gemini-3.8-flash": "Gemini 3.8 Flash", "haiku-4-5": "Haiku 4.5"}
SHORT = {"opus-5": "Opus 5", "gemini-4-argon": "Argon", "deepseek-v4.1-flash-1017": "DeepSeek", "gpt-6.1-sol": "Sol",
         "gpt-6-luna": "Luna", "kimi-k3": "Kimi K3", "sonnet-5": "Sonnet 5", "sonnet-4-6": "Sonnet 4.6",
         "gemini-3.8-flash": "Flash 3.8", "haiku-4-5": "Haiku 4.5"}
COLOR = {"opus-5": "#b4700a", "sonnet-5": "#e07b39", "sonnet-4-6": "#ef9f5f", "haiku-4-5": "#f3c48e",
         "gemini-4-argon": "#1c5cab", "gemini-3.8-flash": "#6da7ec", "gpt-6.1-sol": "#117a52", "gpt-6-luna": "#5fc08f",
         "deepseek-v4.1-flash-1017": "#7b4fb3", "kimi-k3": "#1e9aa8"}
INK, MUTED, GRID, RULE, SHADE = "#0b0b0b", "#52514e", "#e6e5e1", "#c3c2b7", "#fbe9e7"
CUECOL = {"crossfield": "#2a78d6", "recall": "#eb6834", "rule": "#1baf7a", "none": "#9a9891"}
PF_FIELDS = ["length", "mass", "organism", "gene_symbol"]
CF_FIELDS = ["molecular_weight", "heavy_atom_count", "h_bond_donors", "name"]
FLABEL = {"length": "length", "mass": "mass", "organism": "organism", "gene_symbol": "gene symbol",
          "molecular_weight": "mol. weight", "heavy_atom_count": "heavy atoms", "h_bond_donors": "H-bond donors", "name": "name"}
FSHORT = {"length": "length", "mass": "mass", "organism": "organism", "gene_symbol": "gene sym.",
          "molecular_weight": "mol. wt", "heavy_atom_count": "heavy at.", "h_bond_donors": "HBD", "name": "name"}
CUES = [("crossfield", "cross-field"), ("recall", "recall"), ("rule", "rule"), ("none", "unspecific")]

plt.rcParams.update({
    "font.family": "sans-serif", "font.serif": ["Arial", "Arial", "Arial", "DejaVu Serif"],
    "font.size": 7.5, "axes.titlesize": 7.8, "axes.labelsize": 7.2, "xtick.labelsize": 6.6, "ytick.labelsize": 6.6,
    "legend.fontsize": 6.4, "axes.edgecolor": RULE, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "pdf.fonttype": 42, "ps.fonttype": 42})


# ------------------------------------------------------------------ data
def norm(m):
    return re.sub(r"^claude-", "", m.split(":")[-1].split("/")[-1].lower())


def rows(globs, chem=False):
    out = []
    for r in load_runs([str(ROOT / g) for g in globs]):
        s = score(r); s["m"] = norm(s["model"])
        s.update({f"cue_{k}": v for k, v in classify(s["concerns"], chem=chem).items()})
        s["cue_none"] = not (s["cue_crossfield"] or s["cue_recall"] or s["cue_rule"])
        out.append(s)
    return out


SWEEP_GLOBS = [g for g in ["results/sweep_traces*.jsonl", "results/sweep/*.jsonl"] if glob.glob(str(ROOT / g))]
P = rows(["results/v2/traces_*.jsonl"]); PF = rows(["results/v2_full/traces_*.jsonl"])
C = rows(["results/chem/traces_*.jsonl"], chem=True); CF = rows(["results/chem_full/traces_*.jsonl"], chem=True)
SW = rows(SWEEP_GLOBS) if SWEEP_GLOBS else []
for r in SW:
    mm = re.match(r"f([\d.]+)_(consistent|inconsistent)", r["base_condition"] or "")
    r["factor"], r["arm"] = (float(mm.group(1)), mm.group(2)) if mm else (None, None)
TASKDIR = {t["task_id"]: t.get("direction") for t in json.loads((ROOT / "data" / "tasks_v2.json").read_text())["tasks"]}
print(f"rows: protein {len(P)}, protein-full {len(PF)}, chem {len(C)}, chem-full {len(CF)}, sweep {len(SW)}")


def sel(rs, m=None, cond=None, verify=None, field=None, tasks=None):
    return [r for r in rs if (m is None or r["m"] == m) and (cond is None or r["base_condition"] == cond)
            and (verify is None or bool(r["verify_prompt"]) == verify) and (field is None or r["target_field"] == field)
            and (tasks is None or r["task_id"] in tasks)]


def rate(rs, k="propagated"):
    rs = list(rs); return sum(bool(r[k]) for r in rs) / len(rs) if rs else float("nan")


def both(rs):
    rs = list(rs); return sum(bool(r["flagged"]) and bool(r["propagated"]) for r in rs) / len(rs) if rs else float("nan")


def wilson(k, n, z=1.96):
    if not n: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def ci(rs, k="propagated"):
    rs = list(rs); return wilson(sum(bool(r[k]) for r in rs), len(rs))


def style(ax, ylabel=None, ylim=(0, 1.0), xpct=False, xmax=1.02):
    ax.yaxis.grid(True, color=GRID, linewidth=0.6, zorder=0); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(RULE); ax.tick_params(axis="both", length=0)
    if ylim:
        ax.set_ylim(*ylim); ax.set_yticks([0, .25, .5, .75, 1]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    if xpct:
        ax.set_xlim(-0.02, xmax); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
        ax.xaxis.grid(True, color=GRID, lw=0.6); ax.yaxis.grid(False)
    if ylabel: ax.set_ylabel(ylabel)


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", pad_inches=0.02, dpi=250); plt.close(fig)


def model_handles(models):
    return [Line2D([], [], marker="o", ls="", ms=4.0, mfc=COLOR[m], mec=COLOR[m], label=LABEL[m]) for m in models]


N = {}


# ------------------------------------------------------------------ F0 pipeline schematic
def fig_design():
    fig, ax = plt.subplots(figsize=(TW, 1.95)); ax.set_xlim(0, 100); ax.set_ylim(0, 50); ax.axis("off")

    def box(x, y, w, h, title, lines, fc="#f7f7f5", ec=RULE, tc=INK, fs=6.2):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2", fc=fc, ec=ec, lw=0.8, zorder=2))
        ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="center", fontsize=6.9, weight="bold", color=tc, zorder=3)
        for i, l in enumerate(lines):
            ax.text(x + 1.6, y + h - 8.2 - 4.6 * i, l, ha="left", va="center", fontsize=fs, color=tc, zorder=3)

    def arrow(x0, x1, y):
        ax.annotate("", (x1, y), (x0, y), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8, shrinkA=0, shrinkB=0), zorder=1)

    box(0.5, 24, 19.5, 25, "Real records", ["UniProt: 300 human proteins, 7 fields", "PubChem: 300 compounds, 5 fields",
                                             "summary or full database entry", "seeded, cached, byte-identical"])
    box(22.5, 24, 19.5, 25, "300 tasks, 10 templates", ["threshold · ratio · comparison · lookup", "gold vs corrupted-implied answer",
                                                          "verified to differ, 5% margin", "shrink | inflate direction split"])
    box(44.5, 24, 22, 25, "Tool-use agent", ["system prompt (+verify)", "get_protein · find_protein_by_gene",
                                               "get_compound · find_compound_by_name", "≤ 8 rounds · 10 models · 5 vendors"])
    box(69, 24, 30.5, 25, "Final JSON → grader", ["{\"answer\": …, \"concerns\": […]}", "correct · propagated · flagged · silent",
                                                     "cue labels: cross-field · recall · rule", "Wilson CI · task-cluster bootstrap"])
    for x0, x1 in ((20, 22.5), (42, 44.5), (66.5, 69)): arrow(x0, x1, 36.5)
    box(28, 1, 27, 19, "Corrupting tool layer", ["one field of one record per task;", "all other bytes identical. No error,", "no warning, no schema change."], fc="#fdf1ef", ec="#d94a3d", tc="#8a2b22")
    ax.annotate("", (55.5, 24), (47, 20), arrowprops=dict(arrowstyle="-|>", color="#d94a3d", lw=0.8), zorder=1)
    ex = [("clean", INK, "Q6UW63: 502 aa · 58,043 Da · Homo sapiens      CID 3671: 230.31 Da · 17 heavy atoms · 0 donors"),
          ("impossible", "#d94a3d", "3 aa · 58,043 Da · E. coli K-12 (nucleus)      2 Da · 50,000 atoms · −3 donors · ‘Fenvaxide’"),
          ("plausible", "#e07b39", "376 aa · 43,532 Da · Mus musculus      184.25 Da · 14 atoms · 1 donor · ‘Anthracene’"),
          ("sweep", "#2a78d6", "×0.9 … ×0.005; paired field consistent | inconsistent")]
    for i, (k, c, t) in enumerate(ex):
        ax.text(57.5, 17.5 - 4.4 * i, f"{k}:", fontsize=6.0, color=c, weight="bold", va="center")
        ax.text(65.5, 17.5 - 4.4 * i, t, fontsize=5.7, color=INK, va="center")
    ax.text(0.5, 17.5, "Tools read from disk. The only signal\navailable to the agent is the value itself.", fontsize=6.0, color=MUTED, va="top")
    save(fig, "icml_design")


# ------------------------------------------------------------------ F1 noticing vs answering: stacked bars
def fig_main():
    panels = [("(a) proteins, impossible", P, "impossible", False), ("(b) proteins, plausible", P, "plausible", False),
              ("(c) molecules, impossible", C, "impossible", None), ("(d) molecules, plausible", C, "plausible", None)]
    fig, axes = plt.subplots(1, 4, figsize=(TW, 2.55), sharey=True, gridspec_kw={"wspace": 0.1})
    n = len(ORDER)
    for ax, (title, D, cond, v) in zip(axes, panels):
        for i, m in enumerate(ORDER):
            y = n - 1 - i
            rs = sel(D, m, cond, v); fl, pr, fp = rate(rs, "flagged"), rate(rs), both(rs)
            ax.barh(y, fp, color=COLOR[m], height=0.66, zorder=3)
            ax.barh(y, pr - fp, left=fp, color=COLOR[m], alpha=0.3, height=0.66, zorder=3)
            ax.plot([fl, fl], [y - 0.45, y + 0.45], color=INK, lw=1.2, zorder=4)
            ax.text(1.05, y, f"{100*pr:.0f}", va="center", ha="left", fontsize=6.2, color=INK, zorder=5)
            N[f"main|{title[4:]}|{m}"] = {"flagged": fl, "propagated": pr, "flagged_and_propagated": fp, "n": len(rs)}
        ax.set_yticks(range(n)); ax.set_yticklabels([LABEL[m] for m in reversed(ORDER)])
        ax.set_ylim(-0.6, n - 0.4)
        style(ax, ylim=None, xpct=True, xmax=1.24); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0", "50", "100%"])
        ax.set_title(title, loc="left", weight="bold"); ax.set_xlabel("share of runs")
    hl = [Patch(fc=MUTED, label="relayed and flagged (noticed, yet answered)"), Patch(fc=MUTED, alpha=0.3, label="relayed without a flag"),
          Line2D([], [], color=INK, lw=1.2, label="flag rate")]
    fig.legend(handles=hl, loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, handlelength=1.2, columnspacing=1.5)
    save(fig, "icml_main")


# ------------------------------------------------------------------ F2 sweep
def fig_sweep():
    if not SW: print("no sweep traces; skipping"); return
    factors = sorted({r["factor"] for r in SW if r["factor"]}, reverse=True)
    models = [m for m in ORDER if sel(SW, m)]
    fig, axes = plt.subplots(1, 2, figsize=(TW, 2.05), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, arm, title in zip(axes, ("consistent", "inconsistent"), ("(a) record kept consistent", "(b) record made inconsistent")):
        for m in models:
            ys = [rate([r for r in SW if r["m"] == m and r["arm"] == arm and r["factor"] == f]) for f in factors]
            ax.plot(range(len(factors)), ys, "-o", color=COLOR[m], lw=1.1, ms=3.0, zorder=3, label=LABEL[m])
            N[f"sweep|{m}|{arm}"] = dict(zip([f"{f:g}" for f in factors], ys))
        ax.set_xticks(range(len(factors))); ax.set_xticklabels([f"×{f:g}" for f in factors])
        style(ax, ylim=(-0.02, 1.05)); ax.set_title(title, loc="left", weight="bold")
        ax.set_xlabel("factor applied to the true length or mass (more severe →)")
    axes[0].set_ylabel("corrupted value in final answer")
    axes[0].text(0.02, 0.05, "flag rate 100% at ×0.005 for every model;\nrecords describe 1–5-residue, 100–600 Da proteins", transform=axes[0].transAxes, fontsize=5.9, color=MUTED, va="bottom")
    axes[1].text(0.02, 0.05, "paired field unchanged; the corrupted\none can be recomputed from it", transform=axes[1].transAxes, fontsize=5.9, color=MUTED, va="bottom")
    fig.legend(handles=model_handles(models), loc="lower center", bbox_to_anchor=(0.5, -0.17), ncol=5, frameon=False, handlelength=0.8, columnspacing=1.2)
    save(fig, "icml_sweep")


# ------------------------------------------------------------------ F3 mechanism: direction, cue → repair, route class
ROUTE = {("protein", "summary", "length"): "partner field", ("protein", "summary", "mass"): "partner field",
         ("protein", "summary", "organism"): "none", ("protein", "summary", "gene_symbol"): "re-query only",
         ("protein", "full", "length"): "exact derivation", ("protein", "full", "mass"): "exact derivation",
         ("protein", "full", "organism"): "exact derivation", ("protein", "full", "gene_symbol"): "re-query only",
         ("chem", "summary", "molecular_weight"): "partner field", ("chem", "summary", "heavy_atom_count"): "partner field",
         ("chem", "summary", "h_bond_donors"): "none", ("chem", "summary", "name"): "re-query only",
         ("chem", "full", "molecular_weight"): "exact derivation", ("chem", "full", "heavy_atom_count"): "exact derivation",
         ("chem", "full", "h_bond_donors"): "exact derivation", ("chem", "full", "name"): "re-query only"}
ROUTE_ORDER = ["none", "re-query only", "partner field", "exact derivation"]


def fig_mechanism():
    fig, axes = plt.subplots(1, 3, figsize=(TW, 2.55), gridspec_kw={"width_ratios": [1.0, 1.0, 1.05], "wspace": 0.5})
    n = len(ORDER)
    # (a) direction split
    ax = axes[0]
    for i, m in enumerate(ORDER):
        y = n - 1 - i
        rs = [r for r in sel(P, m, "impossible", False) if r["target_field"] in ("length", "mass")]
        a = rate([r for r in rs if TASKDIR.get(r["task_id"]) == "shrink"]); b = rate([r for r in rs if TASKDIR.get(r["task_id"]) == "inflate"])
        ax.plot([a, b], [y, y], color=COLOR[m], lw=1.3, alpha=0.75, zorder=2)
        ax.plot(a, y, "o", ms=4.4, mfc=COLOR[m], mec=COLOR[m], zorder=3); ax.plot(b, y, "^", ms=4.8, mfc="white", mec=COLOR[m], mew=1.0, zorder=4)
        N[f"direction|{m}"] = {"shrink": a, "inflate": b}
    ax.set_yticks(range(n)); ax.set_yticklabels([SHORT[m] for m in reversed(ORDER)]); ax.set_ylim(-0.6, n - 0.4)
    style(ax, ylim=None, xpct=True); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0", "50", "100%"])
    ax.set_title("(a) shrink vs inflate", loc="left", weight="bold"); ax.set_xlabel("propagation, impossible length/mass")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", ms=4, mfc=MUTED, mec=MUTED, label="shrink"),
                       Line2D([], [], marker="^", ls="", ms=4.6, mfc="white", mec=MUTED, label="inflate")],
              loc="lower left", frameon=False, handlelength=0.8, borderaxespad=0.1, ncol=2, columnspacing=0.8)
    # (b) propagation given cited cue
    ax = axes[1]
    groups = [("prot.\nimp.", sel(P, cond="impossible", verify=False)), ("chem.\nimp.", sel(C, cond="impossible")),
              ("sweep\ninc.", [r for r in SW if r["arm"] == "inconsistent"]), ("prot.\nplaus.", sel(P, cond="plausible", verify=False)),
              ("chem.\nplaus.", sel(C, cond="plausible"))]
    for j, (g, D) in enumerate(groups):
        D = [r for r in D if r["flagged"]]
        for k, (cue, lab) in enumerate(CUES[:3]):
            sub = [r for r in D if r[f"cue_{cue}"]]
            if len(sub) < 10: continue
            y = rate(sub); lo, hi = ci(sub); x = j + (k - 1) * 0.24
            ax.plot([x, x], [lo, hi], color=CUECOL[cue], lw=0.9, alpha=0.6, zorder=2)
            ax.plot(x, y, "o", ms=4.4, mfc=CUECOL[cue], mec=CUECOL[cue], zorder=3)
            N[f"cueprop|{g.replace(chr(10), ' ')}|{cue}"] = {"propagated": y, "n": len(sub)}
    ax.set_xticks(range(len(groups))); ax.set_xticklabels([g for g, _ in groups], fontsize=6.4); ax.set_xlim(-0.6, len(groups) - 0.4)
    style(ax, ylim=(-0.02, 1.05)); ax.set_title("(b) propagation by cited cue", loc="left", weight="bold")
    ax.set_ylabel("propagation among flagged runs")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", ms=4, mfc=CUECOL[c], mec=CUECOL[c], label=l) for c, l in CUES[:3]],
              loc="lower center", bbox_to_anchor=(0.5, -0.42), frameon=False, handlelength=0.8, ncol=3, columnspacing=1.0)
    # (c) route class
    ax = axes[2]
    import random; rng = random.Random(0)
    pts = []
    for dom, S, F, fields in (("protein", P, PF, PF_FIELDS), ("chem", C, CF, CF_FIELDS)):
        full_models = [m for m in ORDER if sel(F, m)]
        for m in ORDER:
            for f in fields:
                rs = sel(S, m, "impossible", False if dom == "protein" else None, f)
                if rs: pts.append((ROUTE[(dom, "summary", f)], rate(rs), dom, "summary"))
        for m in full_models:
            for f in fields:
                pts.append((ROUTE[(dom, "full", f)], rate(sel(F, m, "impossible", None, f)), dom, "full"))
    for route, y, dom, fmt in pts:
        x = ROUTE_ORDER.index(route) + rng.uniform(-0.24, 0.24)
        ax.plot(x, y, "o" if dom == "protein" else "s", ms=3.4, mfc="#2a78d6" if fmt == "summary" else "#eb6834", mec="none", alpha=0.75, zorder=3)
    for j, route in enumerate(ROUTE_ORDER):
        ys = sorted(y for r, y, *_ in pts if r == route); med = ys[len(ys) // 2]
        ax.plot([j - 0.32, j + 0.32], [med, med], color=INK, lw=1.3, zorder=4)
        N[f"route|{route}"] = {"n_cells": len(ys), "median": med, "mean": sum(ys) / len(ys)}
    ax.set_xticks(range(len(ROUTE_ORDER))); ax.set_xticklabels(["none", "re-query\nonly", "partner\nfield", "exact\nderivation"], fontsize=6.4); ax.set_xlim(-0.6, len(ROUTE_ORDER) - 0.4)
    style(ax, ylim=(-0.02, 1.05)); ax.set_title("(c) propagation by route", loc="left", weight="bold")
    ax.set_ylabel("impossible-value propagation, per model × field")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", ms=3.6, mfc="#2a78d6", mec="none", label="protein, summary record"),
                       Line2D([], [], marker="o", ls="", ms=3.6, mfc="#eb6834", mec="none", label="protein, full record"),
                       Line2D([], [], marker="s", ls="", ms=3.4, mfc="#2a78d6", mec="none", label="molecule, summary record"),
                       Line2D([], [], marker="s", ls="", ms=3.4, mfc="#eb6834", mec="none", label="molecule, full record"),
                       Line2D([], [], color=INK, lw=1.3, label="median")],
              loc="lower center", bbox_to_anchor=(0.5, -0.5), frameon=False, handlelength=0.8, ncol=2, columnspacing=0.8, labelspacing=0.3)
    save(fig, "icml_mechanism")


# ------------------------------------------------------------------ F4 cue heatmaps (appendix)
def fig_cues():
    groups = [("protein, impossible", sel(P, cond="impossible", verify=False)), ("protein, plausible", sel(P, cond="plausible", verify=False)),
              ("sweep, consistent", [r for r in SW if r["arm"] == "consistent"]), ("sweep, inconsistent", [r for r in SW if r["arm"] == "inconsistent"]),
              ("chemistry, impossible", sel(C, cond="impossible")), ("chemistry, plausible", sel(C, cond="plausible"))]
    fig, axes = plt.subplots(2, 3, figsize=(TW, 4.4), gridspec_kw={"wspace": 0.08, "hspace": 0.5})
    for ax, (title, D) in zip(axes.flat, groups):
        D = [r for r in D if r["flagged"]]
        M = [[rate([r for r in D if r["m"] == m], f"cue_{k}") if sel(D, m) else float("nan") for k, _ in CUES] for m in ORDER]
        ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i, m in enumerate(ORDER):
            for j, (k, _) in enumerate(CUES):
                v = M[i][j]
                ax.text(j, i, "–" if math.isnan(v) else f"{100*v:.0f}", ha="center", va="center", fontsize=6.3,
                        color=MUTED if math.isnan(v) else ("white" if v > 0.55 else INK))
                N[f"cue|{title}|{m}|{k}"] = v
        ax.set_xticks(range(len(CUES))); ax.set_xticklabels([l for _, l in CUES], fontsize=6.3); ax.set_yticks(range(len(ORDER)))
        ax.set_yticklabels([LABEL[m] for m in ORDER] if ax in (axes[0][0], axes[1][0]) else [""] * len(ORDER))
        ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
        ax.set_title(f"{title}\n$n$ = {len(D)} flagged runs", loc="left", fontsize=7.0, weight="bold")
    save(fig, "icml_cues")


# ------------------------------------------------------------------ F5 record redundancy
def fig_redundancy():
    panels = [("(a) proteins, impossible", P, PF, PF_FIELDS, "impossible"), ("(b) proteins, plausible", P, PF, PF_FIELDS, "plausible"),
              ("(c) molecules, impossible", C, CF, CF_FIELDS, "impossible"), ("(d) molecules, plausible", C, CF, CF_FIELDS, "plausible")]
    fig, axes = plt.subplots(1, 4, figsize=(TW, 2.75), gridspec_kw={"wspace": 0.95})
    for ax, (title, S, F, fields, cond) in zip(axes, panels):
        models = [m for m in ORDER if sel(F, m)]; tasks = {r["task_id"] for r in F}
        labels, y = [], 0
        for k, m in enumerate(models):
            for f in fields:
                a = rate(sel(S, m, cond, False if S is P else None, f, tasks)); b = rate(sel(F, m, cond, None, f))
                ax.plot([a, b], [y, y], color=COLOR[m], lw=1.2, alpha=0.7, zorder=2)
                ax.plot(a, y, "o", ms=4.0, mfc=COLOR[m], mec=COLOR[m], zorder=3); ax.plot(b, y, "o", ms=4.0, mfc="white", mec=COLOR[m], mew=1.0, zorder=4)
                N[f"redundancy|{title[4:]}|{m}|{f}"] = {"summary": a, "full": b}
                labels.append(f"{SHORT[m]} · {FSHORT[f]}"); y += 1
            if k < len(models) - 1:
                ax.axhline(y - 0.5, color=GRID, lw=0.7, zorder=1)
        ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=6.0); ax.invert_yaxis()
        style(ax, ylim=None, xpct=True); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0", "50", "100%"])
        ax.set_title(title, loc="left", weight="bold"); ax.set_xlabel("propagation")
    hl = [Line2D([], [], marker="o", ls="", ms=4.0, mfc=MUTED, mec=MUTED, label="summary record"), Line2D([], [], marker="o", ls="", ms=4.0, mfc="white", mec=MUTED, label="full database record")]
    fig.legend(handles=hl, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False, handlelength=0.8)
    save(fig, "icml_redundancy")


# ------------------------------------------------------------------ F6 verification sentence
def fig_verify():
    fig, axes = plt.subplots(1, 2, figsize=(TW, 2.3), sharey=True, gridspec_kw={"wspace": 0.35})
    n = len(ORDER)
    for ax, cond, title in zip(axes, ("impossible", "plausible"), ("(a) impossible corruptions", "(b) plausible corruptions")):
        for i, m in enumerate(ORDER):
            y = n - 1 - i
            a, b = rate(sel(P, m, cond, False)), rate(sel(P, m, cond, True))
            fa, fb = rate(sel(P, m, cond, False), "flagged"), rate(sel(P, m, cond, True), "flagged")
            ax.plot([a, b], [y, y], color=COLOR[m], lw=1.4, alpha=0.75, zorder=2)
            ax.plot(a, y, "o", ms=4.6, mfc=COLOR[m], mec=COLOR[m], zorder=3); ax.plot(b, y, "o", ms=4.6, mfc="white", mec=COLOR[m], mew=1.1, zorder=4)
            ax.text(1.05, y, f"{100*a:.0f} → {100*b:.0f}", fontsize=6.2, color=INK, va="center")
            N[f"verify|{m}|{cond}"] = {"baseline": a, "verify": b, "flag_baseline": fa, "flag_verify": fb}
        ax.set_yticks(range(n)); ax.set_yticklabels([LABEL[m] for m in reversed(ORDER)]); ax.set_ylim(-0.6, n - 0.4)
        style(ax, ylim=None, xpct=True, xmax=1.3); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
        ax.set_title(title, loc="left", weight="bold"); ax.set_xlabel("corrupted value in final answer")
    hl = [Line2D([], [], marker="o", ls="", ms=4.2, mfc=MUTED, mec=MUTED, label="baseline prompt"), Line2D([], [], marker="o", ls="", ms=4.2, mfc="white", mec=MUTED, label="+verify")]
    fig.legend(handles=hl, loc="lower center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, handlelength=0.8)
    save(fig, "icml_verify")


# ------------------------------------------------------------------ F7 appendix heatmap
def fig_heatmap():
    fig, axes = plt.subplots(1, 2, figsize=(TW, 3.5), gridspec_kw={"wspace": 0.9})
    for ax, (D, fields, title, v) in zip(axes, [(P, PF_FIELDS, "proteins (baseline prompt)", False), (C, CF_FIELDS, "small molecules", None)]):
        rows_, labels = [], []
        for m in ORDER:
            for cond in ("impossible", "plausible"):
                rows_.append([rate(sel(D, m, cond, v, f)) for f in fields]); labels.append(f"{LABEL[m]} · {cond}")
        ax.imshow(rows_, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i, rw in enumerate(rows_):
            for j, val in enumerate(rw):
                ax.text(j, i, f"{100*val:.0f}", ha="center", va="center", fontsize=6.2, color="white" if val > 0.55 else INK)
        ax.set_xticks(range(len(fields))); ax.set_xticklabels([FSHORT[f] for f in fields]); ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=6.0)
        ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]; ax.set_title(title, loc="left", weight="bold")
    save(fig, "icml_heatmap")


# ------------------------------------------------------------------ tables
def pct(x): return "--" if (x is None or (isinstance(x, float) and math.isnan(x))) else f"{100*x:.0f}"


def tex_table(path, lines): (TAB / path).write_text("\n".join(lines) + "\n")


def table_main():
    L = [r"\begin{tabular}{lrrrrrrrr}", r"\toprule", r"& \multicolumn{4}{c}{baseline prompt} & \multicolumn{4}{c}{+verify} \\", r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}",
         r"& \multicolumn{2}{c}{impossible} & \multicolumn{2}{c}{plausible} & \multicolumn{2}{c}{impossible} & \multicolumn{2}{c}{plausible} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}",
         r"model & flagged & propagated & flagged & propagated & flagged & propagated & flagged & propagated \\", r"\midrule"]
    for m in ORDER:
        cells = []
        for v in (False, True):
            for cond in ("impossible", "plausible"):
                rs = sel(P, m, cond, v); lo, hi = ci(rs)
                cells += [pct(rate(rs, "flagged")), f"{pct(rate(rs))} [{pct(lo)},{pct(hi)}]"]
        L.append(f"{LABEL[m]} & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_main_results.tex", L)


def table_chem():
    L = [r"\begin{tabular}{lrrrrrr}", r"\toprule", r"& \multicolumn{3}{c}{impossible} & \multicolumn{2}{c}{plausible} & clean \\", r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}\cmidrule(lr){7-7}",
         r"model & flagged & prop. & both & flagged & prop. & flagged \\", r"\midrule"]
    for m in ORDER:
        i, pl, cl = sel(C, m, "impossible"), sel(C, m, "plausible"), sel(C, m, "clean")
        L.append(f"{LABEL[m]} & {pct(rate(i,'flagged'))} & {pct(rate(i))} & {pct(both(i))} & {pct(rate(pl,'flagged'))} & {pct(rate(pl))} & {pct(rate(cl,'flagged'))} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_chem_main.tex", L)


def table_redundancy():
    L = [r"\begin{tabular}{llrrrr}", r"\toprule", r"& & \multicolumn{2}{c}{impossible} & \multicolumn{2}{c}{plausible} \\", r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
         r"model & field & summary & full & summary & full \\", r"\midrule"]
    for S, F, fields, dom in ((P, PF, PF_FIELDS, "proteins"), (C, CF, CF_FIELDS, "molecules")):
        tasks = {r["task_id"] for r in F}
        L.append(r"\multicolumn{6}{l}{\emph{" + dom + r"}} \\")
        for m in [m for m in ORDER if sel(F, m)]:
            for k, f in enumerate(fields):
                cells = [pct(rate(sel(S, m, c, False if S is P else None, f, tasks))) + " & " + pct(rate(sel(F, m, c, None, f))) for c in ("impossible", "plausible")]
                L.append(f"{LABEL[m] if k == 0 else ''} & {FLABEL[f]} & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_redundancy.tex", L)


def table_taxonomy():
    groups = [("protein, impossible", sel(P, cond="impossible", verify=False)), ("protein, plausible", sel(P, cond="plausible", verify=False)),
              ("sweep, consistent", [r for r in SW if r["arm"] == "consistent"]), ("sweep, inconsistent", [r for r in SW if r["arm"] == "inconsistent"]),
              ("chemistry, impossible", sel(C, cond="impossible")), ("chemistry, plausible", sel(C, cond="plausible"))]
    L = [r"\begin{tabular}{lrrrrrrrr}", r"\toprule", r"& & \multicolumn{4}{c}{share of flagged runs citing} & \multicolumn{3}{c}{propagation given cue} \\", r"\cmidrule(lr){3-6}\cmidrule(lr){7-9}",
         r"flagged runs & $n$ & cross-field & recall & rule & none & cross-field & recall & rule \\", r"\midrule"]
    for name, D in groups:
        D = [r for r in D if r["flagged"]]
        if not D: continue
        shares = [pct(rate(D, f"cue_{k}")) for k, _ in CUES]; props = [pct(rate([r for r in D if r[f"cue_{k}"]])) for k, _ in CUES[:3]]
        L.append(f"{name} & {len(D)} & " + " & ".join(shares) + " & " + " & ".join(props) + r" \\")
        N[f"taxonomy|{name}"] = {"n": len(D), **{k: rate(D, f"cue_{k}") for k, _ in CUES}}
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_taxonomy.tex", L)


def table_sweep():
    if not SW: return
    L = [r"\begin{tabular}{lrrrr}", r"\toprule", r"& \multicolumn{2}{c}{consistent, $\times 0.005$} & \multicolumn{2}{c}{inconsistent, $\times 0.005$} \\", r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
         r"model & flagged & propagated & flagged & propagated \\", r"\midrule"]
    for m in [m for m in ORDER if sel(SW, m)]:
        cells = []
        for arm in ("consistent", "inconsistent"):
            D = [r for r in SW if r["m"] == m and r["arm"] == arm and r["factor"] == 0.005]; cells += [pct(rate(D, "flagged")), pct(rate(D))]
        L.append(f"{LABEL[m]} & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_sweep.tex", L)


if __name__ == "__main__":
    fig_design(); fig_main(); fig_sweep(); fig_mechanism(); fig_cues(); fig_redundancy(); fig_verify(); fig_heatmap()
    table_main(); table_chem(); table_redundancy(); table_taxonomy(); table_sweep()
    (ROOT / "paper" / "numbers_icml.json").write_text(json.dumps(N, indent=1, default=float))
    print("wrote", sorted(p.name for p in OUT.glob("icml_*.pdf")))
