#!/usr/bin/env python3
"""ICML figures and tables, computed directly from the deduplicated traces via analysis.score/classify.
Writes paper/figures/icml_*.pdf|png, paper/tables/icml_*.tex and paper/numbers_icml.json."""
import glob, json, math, re, sys
from collections import defaultdict
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis import load_runs, score, classify  # noqa: E402

OUT = ROOT / "paper" / "figures"; TAB = ROOT / "paper" / "tables"
OUT.mkdir(exist_ok=True); TAB.mkdir(exist_ok=True)
TW, CW = 6.75, 3.25  # ICML text width / column width, inches

ORDER = ["opus-5", "gemini-4-argon", "deepseek-v4.1-flash-1017", "gpt-6.1-sol", "gpt-6-luna",
         "kimi-k3", "sonnet-5", "sonnet-4-6", "gemini-3.8-flash", "haiku-4-5"]
LABEL = {"opus-5": "Opus 5", "gemini-4-argon": "Gemini 4 Argon", "deepseek-v4.1-flash-1017": "DeepSeek V4.1 Flash",
         "gpt-6.1-sol": "GPT-6.1 Sol", "gpt-6-luna": "GPT-6 Luna", "kimi-k3": "Kimi K3", "sonnet-5": "Sonnet 5",
         "sonnet-4-6": "Sonnet 4.6", "gemini-3.8-flash": "Gemini 3.8 Flash", "haiku-4-5": "Haiku 4.5"}
COLOR = {"opus-5": "#b4700a", "sonnet-5": "#e07b39", "sonnet-4-6": "#ef9f5f", "haiku-4-5": "#f3c48e",
         "gemini-4-argon": "#1c5cab", "gemini-3.8-flash": "#6da7ec", "gpt-6.1-sol": "#117a52", "gpt-6-luna": "#5fc08f",
         "deepseek-v4.1-flash-1017": "#7b4fb3", "kimi-k3": "#1e9aa8"}
INK, MUTED, GRID, RULE, SHADE = "#0b0b0b", "#52514e", "#e6e5e1", "#c3c2b7", "#fbe9e7"
PF_FIELDS = ["length", "mass", "organism", "gene_symbol"]
CF_FIELDS = ["molecular_weight", "heavy_atom_count", "h_bond_donors", "name"]
FLABEL = {"length": "length", "mass": "mass", "organism": "organism", "gene_symbol": "gene symbol",
          "molecular_weight": "mol. weight", "heavy_atom_count": "heavy atoms", "h_bond_donors": "H-bond donors", "name": "name"}
CUES = [("crossfield", "cross-field"), ("recall", "recall"), ("rule", "rule"), ("none", "unspecific")]

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
    "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "xtick.labelsize": 6.8, "ytick.labelsize": 6.8,
    "legend.fontsize": 6.5, "axes.edgecolor": RULE, "text.color": INK, "axes.labelcolor": INK,
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


SWEEP_GLOBS = [g for g in ["results/sweep_traces*.jsonl", "results/sweep/*.jsonl", "results/sweep/traces*.jsonl", "results/v1/sweep*.jsonl"]
               if glob.glob(str(ROOT / g))]
print("sweep globs matched:", SWEEP_GLOBS or "NONE")
P = rows(["results/v2/traces_*.jsonl"])
PF = rows(["results/v2_full/traces_*.jsonl"])
C = rows(["results/chem/traces_*.jsonl"], chem=True)
CF = rows(["results/chem_full/traces_*.jsonl"], chem=True)
SW = rows(SWEEP_GLOBS) if SWEEP_GLOBS else []
for r in SW:
    mm = re.match(r"f([\d.]+)_(consistent|inconsistent)", r["base_condition"] or "")
    r["factor"], r["arm"] = (float(mm.group(1)), mm.group(2)) if mm else (None, None)
print(f"rows: protein {len(P)}, protein-full {len(PF)}, chem {len(C)}, chem-full {len(CF)}, sweep {len(SW)}")


def sel(rs, m=None, cond=None, verify=None, field=None, tasks=None):
    return [r for r in rs if (m is None or r["m"] == m) and (cond is None or r["base_condition"] == cond)
            and (verify is None or bool(r["verify_prompt"]) == verify) and (field is None or r["target_field"] == field)
            and (tasks is None or r["task_id"] in tasks)]


def rate(rs, k="propagated"):
    rs = list(rs); return sum(bool(r[k]) for r in rs) / len(rs) if rs else float("nan")


def wilson(k, n, z=1.96):
    if not n: return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


def ci(rs, k="propagated"):
    rs = list(rs); return wilson(sum(bool(r[k]) for r in rs), len(rs))


def style(ax, ylabel=None, ylim=(0, 1.0), xpct=False):
    ax.yaxis.grid(True, color=GRID, linewidth=0.6, zorder=0); ax.set_axisbelow(True)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(RULE); ax.tick_params(axis="both", length=0)
    if ylim:
        ax.set_ylim(*ylim); ax.set_yticks([0, .25, .5, .75, 1]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    if xpct:
        ax.set_xlim(-0.02, 1.02); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0", "25", "50", "75", "100%"])
    if ylabel: ax.set_ylabel(ylabel)


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", pad_inches=0.02, dpi=250); plt.close(fig)


def legend_handles(models):
    return [Line2D([], [], marker="o", ls="", ms=4.2, mfc=COLOR[m], mec=COLOR[m], label=LABEL[m]) for m in models]


N = {}  # numbers used in the text


# ------------------------------------------------------------------ F1 noticing vs answering, two domains
def fig_main():
    fig, axes = plt.subplots(1, 2, figsize=(TW, 2.45), sharey=True)
    for ax, (title, D, has_verify) in zip(axes, [("(a) proteins, 200 tasks", P, True), ("(b) small molecules, 100 tasks", C, False)]):
        ax.add_patch(Rectangle((0.5, 0.5), 0.52, 0.52, fc=SHADE, ec="none", zorder=0))
        ax.text(0.515, 0.985, "noticed, yet answered", fontsize=6.3, color="#a33a30", va="top", zorder=1)
        ax.text(0.01, 0.985, "not noticed, answered", fontsize=6.3, color=MUTED, va="top")
        ax.text(0.515, 0.015, "noticed and corrected", fontsize=6.3, color=MUTED, va="bottom")
        for m in ORDER:
            c = COLOR[m]
            for cond, mk in (("impossible", "o"), ("plausible", "s")):
                b = sel(D, m, cond, False)
                if not b: continue
                x, y = rate(b, "flagged"), rate(b, "propagated")
                lo, hi = ci(b)
                ax.plot([x, x], [lo, hi], color=c, lw=0.7, alpha=0.55, zorder=2)
                ax.plot(x, y, mk, ms=4.6 if mk == "o" else 4.0, mfc=c if mk == "o" else "white", mec=c, mew=0.9, zorder=4)
                N[f"{title[1]}|{m}|{cond}"] = {"flagged": x, "propagated": y, "ci": [lo, hi], "n": len(b)}
                if has_verify and cond == "impossible":
                    v = sel(D, m, cond, True)
                    if v:
                        xv, yv = rate(v, "flagged"), rate(v, "propagated")
                        ax.annotate("", (xv, yv), (x, y), arrowprops=dict(arrowstyle="-|>", color=c, lw=0.6, alpha=0.7, shrinkA=2, shrinkB=2), zorder=3)
                        ax.plot(xv, yv, "o", ms=4.2, mfc="white", mec=c, mew=0.9, zorder=4)
                        N[f"{title[1]}|{m}|{cond}+verify"] = {"flagged": xv, "propagated": yv, "ci": list(ci(v)), "n": len(v)}
        style(ax, xpct=True); ax.set_title(title, loc="left", weight="bold"); ax.set_xlabel("corruption flagged in concerns")
    axes[0].set_ylabel("corrupted value in final answer")
    hl = legend_handles(ORDER) + [Line2D([], [], marker="o", ls="", ms=4.2, mfc=MUTED, mec=MUTED, label="impossible"),
                                  Line2D([], [], marker="s", ls="", ms=3.8, mfc="white", mec=MUTED, label="plausible"),
                                  Line2D([], [], marker="o", ls="", ms=4.2, mfc="white", mec=MUTED, label="impossible, +verify")]
    fig.legend(handles=hl, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, handlelength=0.8, labelspacing=0.42, borderaxespad=0.2)
    fig.subplots_adjust(wspace=0.08); save(fig, "icml_main")


# ------------------------------------------------------------------ F2 sweep, nine models, two arms
def fig_sweep():
    if not SW: print("no sweep traces; skipping fig_sweep"); return
    factors = sorted({r["factor"] for r in SW if r["factor"]}, reverse=True)
    models = [m for m in ORDER if sel(SW, m)]
    fig, axes = plt.subplots(1, 2, figsize=(TW, 2.3), sharey=True)
    for ax, arm, title in zip(axes, ("consistent", "inconsistent"), ("(a) record kept consistent", "(b) record made inconsistent")):
        for m in models:
            ys = [rate([r for r in SW if r["m"] == m and r["arm"] == arm and r["factor"] == f]) for f in factors]
            ax.plot(range(len(factors)), ys, "-o", color=COLOR[m], lw=1.1, ms=3.2, zorder=3, label=LABEL[m])
            N[f"sweep|{m}|{arm}"] = dict(zip([f"{f:g}" for f in factors], ys))
        ax.set_xticks(range(len(factors))); ax.set_xticklabels([f"{f:g}" for f in factors])
        style(ax, ylim=(-0.02, 1.04)); ax.set_title(title, loc="left", weight="bold")
        ax.set_xlabel("factor applied to the true length or mass (more severe →)")
    axes[0].set_ylabel("corrupted value in final answer")
    axes[0].text(0.02, 0.06, "at ×0.005 the records describe\n1–5-residue, 100–600 Da proteins", transform=axes[0].transAxes, fontsize=6.2, color=MUTED, va="bottom")
    axes[1].text(0.02, 0.06, "paired field unchanged;\nthe corrupted one can be recomputed", transform=axes[1].transAxes, fontsize=6.2, color=MUTED, va="bottom")
    fig.legend(handles=legend_handles(models), loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, handlelength=0.8, labelspacing=0.42, borderaxespad=0.2)
    fig.subplots_adjust(wspace=0.08); save(fig, "icml_sweep")


# ------------------------------------------------------------------ F3 cue composition heatmaps
def fig_cues():
    groups = [("protein, impossible", sel(P, cond="impossible", verify=False)), ("protein, plausible", sel(P, cond="plausible", verify=False)),
              ("sweep, consistent", [r for r in SW if r["arm"] == "consistent"]), ("sweep, inconsistent", [r for r in SW if r["arm"] == "inconsistent"]),
              ("chemistry, impossible", sel(C, cond="impossible")), ("chemistry, plausible", sel(C, cond="plausible"))]
    fig, axes = plt.subplots(2, 3, figsize=(TW, 4.3))
    for ax, (title, D) in zip(axes.flat, groups):
        D = [r for r in D if r["flagged"]]
        M = [[rate([r for r in D if r["m"] == m], f"cue_{k}") if sel(D, m) else float("nan") for k, _ in CUES] for m in ORDER]
        ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i, m in enumerate(ORDER):
            for j, _ in enumerate(CUES):
                v = M[i][j]
                if not math.isnan(v): ax.text(j, i, f"{100*v:.0f}", ha="center", va="center", fontsize=6.3, color="white" if v > 0.55 else INK)
                else: ax.text(j, i, "–", ha="center", va="center", fontsize=6.3, color=MUTED)
            for k, _ in CUES: N[f"cue|{title}|{m}|{k}"] = M[i][[c for c, _ in CUES].index(k)]
        ax.set_xticks(range(len(CUES))); ax.set_xticklabels([l for _, l in CUES]); ax.set_yticks(range(len(ORDER)))
        ax.set_yticklabels([LABEL[m] for m in ORDER] if ax in (axes[0][0], axes[1][0]) else [""] * len(ORDER))
        ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]
        ax.set_title(f"{title} (n = {len(D)} flagged runs)", loc="left", fontsize=7.2, weight="bold")
    fig.subplots_adjust(wspace=0.06, hspace=0.42); save(fig, "icml_cues")


# ------------------------------------------------------------------ F4 record redundancy: per-field propagation, summary vs full
def fig_redundancy():
    panels = [("(a) proteins, impossible", P, PF, PF_FIELDS, "impossible"), ("(b) proteins, plausible", P, PF, PF_FIELDS, "plausible"),
              ("(c) molecules, impossible", C, CF, CF_FIELDS, "impossible"), ("(d) molecules, plausible", C, CF, CF_FIELDS, "plausible")]
    fig, axes = plt.subplots(1, 4, figsize=(TW, 2.9), sharey=False)
    for ax, (title, S, F, fields, cond) in zip(axes, panels):
        models = [m for m in ORDER if sel(F, m)]
        tasks = {r["task_id"] for r in F}
        ylabels, y = [], 0
        for m in models:
            for f in fields:
                a = rate(sel(S, m, cond, False, f, tasks)); b = rate(sel(F, m, cond, None, f))
                ax.plot([a, b], [y, y], color=COLOR[m], lw=1.2, alpha=0.7, zorder=2)
                ax.plot(a, y, "o", ms=4.3, mfc=COLOR[m], mec=COLOR[m], zorder=3); ax.plot(b, y, "o", ms=4.3, mfc="white", mec=COLOR[m], mew=1.0, zorder=4)
                N[f"redundancy|{title[4:]}|{m}|{f}"] = {"summary": a, "full": b, "n_summary": len(sel(S, m, cond, False, f, tasks)), "n_full": len(sel(F, m, cond, None, f))}
                ylabels.append(f"{FLABEL[f]}"); y += 1
            y += 0.7
        ax.set_yticks([i for i in range(len(ylabels) + len(models)) if i not in {len(fields) * (k + 1) + k for k in range(len(models))}][:len(ylabels)])
        ax.set_yticklabels(ylabels); ax.invert_yaxis()
        for k, m in enumerate(models):
            ax.text(-0.02, k * (len(fields) + 0.7) - 0.6, LABEL[m], fontsize=6.6, color=COLOR[m], weight="bold", ha="left", va="center")
        style(ax, ylim=None, xpct=True); ax.xaxis.grid(True, color=GRID, lw=0.6); ax.yaxis.grid(False)
        ax.set_title(title, loc="left", weight="bold"); ax.set_xlabel("propagation")
    hl = [Line2D([], [], marker="o", ls="", ms=4.2, mfc=MUTED, mec=MUTED, label="summary record"), Line2D([], [], marker="o", ls="", ms=4.2, mfc="white", mec=MUTED, label="full database record")]
    fig.legend(handles=hl, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=2, frameon=False, handlelength=0.8)
    fig.subplots_adjust(wspace=0.55); save(fig, "icml_redundancy")


# ------------------------------------------------------------------ F5 what the +verify sentence buys
def fig_verify():
    fig, axes = plt.subplots(1, 2, figsize=(TW, 2.3), sharey=True)
    for ax, cond, title in zip(axes, ("impossible", "plausible"), ("(a) impossible corruptions", "(b) plausible corruptions")):
        for i, m in enumerate(ORDER):
            a, b = rate(sel(P, m, cond, False)), rate(sel(P, m, cond, True))
            fa, fb = rate(sel(P, m, cond, False), "flagged"), rate(sel(P, m, cond, True), "flagged")
            ax.plot([a, b], [i, i], color=COLOR[m], lw=1.3, alpha=0.75, zorder=2)
            ax.plot(a, i, "o", ms=4.6, mfc=COLOR[m], mec=COLOR[m], zorder=3); ax.plot(b, i, "o", ms=4.6, mfc="white", mec=COLOR[m], mew=1.0, zorder=4)
            ax.text(1.03, i, f"{100*a:.0f}→{100*b:.0f}  flag {100*fa:.0f}→{100*fb:.0f}", fontsize=6.0, color=MUTED, va="center", clip_on=False)
            N[f"verify|{m}|{cond}"] = {"baseline": a, "verify": b, "flag_baseline": fa, "flag_verify": fb}
        ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([LABEL[m] for m in ORDER]); ax.invert_yaxis()
        style(ax, ylim=None, xpct=True); ax.xaxis.grid(True, color=GRID, lw=0.6); ax.yaxis.grid(False)
        ax.set_title(title, loc="left", weight="bold"); ax.set_xlabel("corrupted value in final answer")
    hl = [Line2D([], [], marker="o", ls="", ms=4.2, mfc=MUTED, mec=MUTED, label="baseline prompt"), Line2D([], [], marker="o", ls="", ms=4.2, mfc="white", mec=MUTED, label="+verify")]
    fig.legend(handles=hl, loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False, handlelength=0.8)
    fig.subplots_adjust(wspace=0.95); save(fig, "icml_verify")


# ------------------------------------------------------------------ F6 appendix heatmap: model x field
def fig_heatmap():
    fig, axes = plt.subplots(1, 2, figsize=(TW, 3.6), gridspec_kw={"width_ratios": [1, 1]})
    for ax, (D, fields, title) in zip(axes, [(P, PF_FIELDS, "proteins (baseline prompt)"), (C, CF_FIELDS, "small molecules")]):
        rows_, labels = [], []
        for m in ORDER:
            for cond in ("impossible", "plausible"):
                rows_.append([rate(sel(D, m, cond, False, f)) for f in fields]); labels.append(f"{LABEL[m]} · {cond}")
        ax.imshow(rows_, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i, rw in enumerate(rows_):
            for j, v in enumerate(rw):
                ax.text(j, i, f"{100*v:.0f}", ha="center", va="center", fontsize=6.2, color="white" if v > 0.55 else INK)
        ax.set_xticks(range(len(fields))); ax.set_xticklabels([FLABEL[f] for f in fields]); ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
        ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]; ax.set_title(title, loc="left", weight="bold")
    fig.subplots_adjust(wspace=0.75); save(fig, "icml_heatmap")


# ------------------------------------------------------------------ tables
def pct(x): return "--" if (x is None or (isinstance(x, float) and math.isnan(x))) else f"{100*x:.0f}"


def tex_table(path, lines):
    (TAB / path).write_text("\n".join(lines) + "\n")


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
         r"model & flagged & propagated & flagged\,\&\,prop. & flagged & propagated & flagged \\", r"\midrule"]
    for m in ORDER:
        i, pl, cl = sel(C, m, "impossible"), sel(C, m, "plausible"), sel(C, m, "clean")
        fp = sum(bool(r["flagged"]) and bool(r["propagated"]) for r in i) / len(i)
        L.append(f"{LABEL[m]} & {pct(rate(i,'flagged'))} & {pct(rate(i))} & {pct(fp)} & {pct(rate(pl,'flagged'))} & {pct(rate(pl))} & {pct(rate(cl,'flagged'))} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_chem_main.tex", L)


def table_redundancy():
    L = [r"\begin{tabular}{llrrrr}", r"\toprule", r"& & \multicolumn{2}{c}{impossible} & \multicolumn{2}{c}{plausible} \\", r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}",
         r"model & field & summary & full & summary & full \\", r"\midrule"]
    for S, F, fields, dom in ((P, PF, PF_FIELDS, "proteins"), (C, CF, CF_FIELDS, "molecules")):
        tasks = {r["task_id"] for r in F}
        L.append(r"\multicolumn{6}{l}{\emph{" + dom + r"}} \\")
        for m in [m for m in ORDER if sel(F, m)]:
            for k, f in enumerate(fields):
                cells = [pct(rate(sel(S, m, c, False, f, tasks))) + " & " + pct(rate(sel(F, m, c, None, f))) for c in ("impossible", "plausible")]
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
        shares = [pct(rate(D, f"cue_{k}")) for k, _ in CUES]
        props = [pct(rate([r for r in D if r[f"cue_{k}"]])) for k, _ in CUES[:3]]
        L.append(f"{name} & {len(D)} & " + " & ".join(shares) + " & " + " & ".join(props) + r" \\")
        N[f"taxonomy|{name}"] = {"n": len(D), **{k: rate(D, f"cue_{k}") for k, _ in CUES}, **{f"prop_{k}": rate([r for r in D if r[f"cue_{k}"]]) for k, _ in CUES[:3]}}
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_taxonomy.tex", L)


def table_sweep():
    if not SW: return
    models = [m for m in ORDER if sel(SW, m)]
    L = [r"\begin{tabular}{lrrrr}", r"\toprule", r"& \multicolumn{2}{c}{consistent, $\times 0.005$} & \multicolumn{2}{c}{inconsistent, $\times 0.005$} \\", r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
         r"model & flagged & propagated & flagged & propagated \\", r"\midrule"]
    for m in models:
        cells = []
        for arm in ("consistent", "inconsistent"):
            D = [r for r in SW if r["m"] == m and r["arm"] == arm and r["factor"] == 0.005]
            cells += [pct(rate(D, "flagged")), pct(rate(D))]
        L.append(f"{LABEL[m]} & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}"]; tex_table("icml_sweep.tex", L)


if __name__ == "__main__":
    fig_main(); fig_sweep(); fig_cues(); fig_redundancy(); fig_verify(); fig_heatmap()
    table_main(); table_chem(); table_redundancy(); table_taxonomy(); table_sweep()
    (ROOT / "paper" / "numbers_icml.json").write_text(json.dumps(N, indent=1, default=float))
    print("wrote", sorted(p.name for p in OUT.glob("icml_*.pdf")), sorted(p.name for p in TAB.glob("icml_*.tex")))
