#!/usr/bin/env python3
"""Publication figures. Drawn at the NeurIPS text width (5.5 in) so fonts print at their true size.
Reads ../results/summary.json and ../results/sweep/summary.json; writes figures/*.pdf (vector) and
figures/*.png (previews) plus numbers.json with every statistic used in the text."""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)
S = json.loads((ROOT / "results" / "summary.json").read_text())
W = json.loads((ROOT / "results" / "sweep" / "summary.json").read_text())

TW = 5.5  # NeurIPS \textwidth in inches
MODELS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-sonnet-5", "claude-opus-5"]
LABEL = {"claude-haiku-4-5": "Haiku 4.5", "claude-sonnet-4-6": "Sonnet 4.6", "claude-sonnet-5": "Sonnet 5", "claude-opus-5": "Opus 5"}
COLOR = {"claude-haiku-4-5": "#2a78d6", "claude-sonnet-4-6": "#eb6834", "claude-sonnet-5": "#1baf7a", "claude-opus-5": "#c98500"}
INK, MUTED, GRID, RULE = "#0b0b0b", "#52514e", "#e6e5e1", "#c3c2b7"
CORRUPT, CLEANC = "#e34948", "#2a78d6"
BLUES = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
CONDS = ["impossible", "plausible", "impossible+verify", "plausible+verify"]
FIELDS = ["length", "mass", "organism", "gene_symbol"]

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.edgecolor": RULE, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "pdf.fonttype": 42, "ps.fonttype": 42,
})


def style(ax, ylabel=None, ylim=(0, 1.0)):
    ax.yaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(RULE)
    ax.tick_params(axis="both", length=0)
    if ylim:
        ax.set_ylim(*ylim)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    if ylabel:
        ax.set_ylabel(ylabel)


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", pad_inches=0.02, dpi=250)
    plt.close(fig)


def bc(m, c):
    return S["by_model_condition"][m].get(c)


# ------------------------------------------------------------------ Figure 1: design schematic
def fig_design():
    fig, ax = plt.subplots(figsize=(TW, 1.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 40); ax.axis("off")

    def box(x, y, w, h, title, lines, fc="#f7f7f5", ec=RULE, tc=INK, lw=0.8, title_c=None, fs=6.6):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.4", fc=fc, ec=ec, lw=lw, zorder=2))
        ax.text(x + w / 2, y + h - 2.0, title, ha="center", va="top", fontsize=7.8, weight="bold", color=title_c or tc, zorder=3)
        for i, ln in enumerate(lines):
            ax.text(x + 1.4, y + h - 6.8 - 4.1 * i, ln, ha="left", va="top", fontsize=fs, color=tc, zorder=3)

    def arrow(x0, y0, x1, y1, color=MUTED, style="-|>", lw=0.9):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=7, color=color, lw=lw, zorder=4))

    Y, H = 17, 23
    box(0, Y, 17, H, "Real records", ["UniProt REST API", "60 Swiss-Prot", "human proteins", "7 fields, seeded"])
    box(19.5, Y, 22, H, "40 tasks, 5 templates", ["length threshold / ratio", "mass comparison", "organism · gene symbol", "gold vs. implied answers"])
    box(44, Y, 25, H, "Tool-use agent", ["system prompt (+verify)", "get_protein(acc)", "find_protein_by_gene(sym)", "≤ 8 rounds · 4 models"])
    box(71.5, Y, 28.5, H, "Final JSON → grader", ['{"answer": …, "concerns": […]}', "correct · propagated · flagged", "silent propagation · recall", "token match · Wilson CI"])
    box(44, 0.5, 25, 12.5, "Corrupting tool layer", ["one field of one record;", "all other bytes identical"], fc="#fdf0ef", ec=CORRUPT, title_c=CORRUPT)
    ym = Y + H / 2
    arrow(17.4, ym, 19.1, ym); arrow(41.9, ym, 43.6, ym); arrow(69.4, ym, 71.1, ym)
    arrow(56.5, 13.4, 56.5, Y - 0.4, color=CORRUPT, style="<|-|>")
    ex = [("clean", "502 aa · 58,043 Da · Homo sapiens", CLEANC),
          ("impossible", "3 aa · 58,043 Da · E. coli K-12 (nucleus)", CORRUPT),
          ("plausible", "376 aa · 43,532 Da · Mus musculus", "#eb6834"),
          ("sweep", "×0.9 … ×0.005; consistent | inconsistent", "#7a6fd6")]
    for i, (name, txt, col) in enumerate(ex):
        y = 11.6 - 3.3 * i
        ax.add_patch(Rectangle((71.5, y - 0.95), 1.6, 1.9, fc=col, ec="none", zorder=3))
        ax.text(74.1, y, f"{name}:", fontsize=6.5, weight="bold", va="center", color=col, zorder=3)
        ax.text(86.5, y, txt, fontsize=6.5, va="center", color=INK, zorder=3)
    for i, ln in enumerate(["Tools read from disk. The only signal", "available to the agent is the value itself:", "no error, no warning, no schema change."]):
        ax.text(0, 11.6 - 3.3 * i, ln, fontsize=6.5, va="center", color=MUTED)
    save(fig, "fig_design")


# ------------------------------------------------------------------ Figure 2: main result
def fig_main():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(TW, 2.0), gridspec_kw={"width_ratios": [1.3, 1]})
    # (a) grouped bars with value labels above the CI
    n = len(MODELS); width = 0.8 / n
    for i, c in enumerate(CONDS):
        gmax = max(bc(m, c)["propagation"]["ci_hi"] for m in MODELS if bc(m, c))
        for j, m in enumerate(MODELS):
            a = bc(m, c)
            if not a:
                continue
            p = a["propagation"]
            x = i - 0.4 + width * (j + 0.5)
            ax.bar([x], [p["rate"]], width=width * 0.9, color=COLOR[m], edgecolor="white", linewidth=0.5,
                   label=LABEL[m] if i == 0 else None, zorder=3)
            ax.errorbar([x], [p["rate"]], yerr=[[max(0, p["rate"] - p["ci_lo"])], [max(0, p["ci_hi"] - p["rate"])]],
                        fmt="none", ecolor=INK, elinewidth=0.6, capsize=1.2, zorder=4)
            # value labels in two rows above the whole group: neighbours never share a row
            ax.text(x, gmax + (0.025 if j % 2 == 0 else 0.085), f"{100 * p['rate']:.0f}", ha="center", va="bottom",
                    fontsize=5.6, color=COLOR[m], zorder=5)
    ax.axvline(1.5, color=RULE, lw=0.7, ls=(0, (2, 2)), zorder=1)
    ax.set_xticks(range(len(CONDS)))
    ax.set_xticklabels(["impossible", "plausible", "impossible\n+ verify", "plausible\n+ verify"])
    style(ax, "corrupted value in final answer", ylim=(0, 1.22))
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    ax.legend(frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.34), handlelength=0.9, columnspacing=0.8)
    ax.set_title("(a) Propagation by model and condition", loc="left", weight="bold")

    # (b) noticed vs answered
    ax2.add_patch(Rectangle((0.5, 0.5), 0.5, 0.5, fc="#fdf0ef", ec="none", zorder=0))
    ax2.text(0.52, 0.52, "noticed, yet\nanswered", ha="left", va="bottom", fontsize=6.4, color=CORRUPT, zorder=1)
    ax2.text(0.02, 0.62, "not noticed,\nanswered", ha="left", va="top", fontsize=6.4, color=MUTED, zorder=1)
    ax2.text(0.52, 0.03, "noticed and\ncorrected", ha="left", va="bottom", fontsize=6.4, color=MUTED, zorder=1)
    for m in MODELS:
        for c in CONDS:
            a = bc(m, c)
            if not a:
                continue
            x, y = a["flag_rate"]["rate"], a["propagation"]["rate"]
            base, verify = c.split("+")[0], c.endswith("+verify")
            marker = "o" if base == "impossible" else "s"
            if verify:
                ax2.scatter([x], [y], s=26, marker=marker, facecolor="white", edgecolor=COLOR[m], linewidth=1.2, zorder=6)
                b = bc(m, base)
                ax2.add_patch(FancyArrowPatch((b["flag_rate"]["rate"], b["propagation"]["rate"]), (x, y), arrowstyle="-|>",
                                              mutation_scale=5, color=COLOR[m], lw=0.7, alpha=0.7, shrinkA=3, shrinkB=3, zorder=4))
            else:
                ax2.scatter([x], [y], s=30, marker=marker, facecolor=COLOR[m], edgecolor="white", linewidth=0.7, zorder=5)
    # direct labels for the baseline-impossible points
    lab = {"claude-haiku-4-5": (0.0, 0.065, "center"), "claude-sonnet-4-6": (0.05, 0.03, "left"),
           "claude-sonnet-5": (0.05, -0.035, "left"), "claude-opus-5": (0.05, 0.0, "left")}
    for m in MODELS:
        a = bc(m, "impossible"); dx, dy, ha = lab[m]
        ax2.text(a["flag_rate"]["rate"] + dx, a["propagation"]["rate"] + dy, LABEL[m], ha=ha, va="center", fontsize=6.2, color=COLOR[m], zorder=7)
    ax2.set_xlim(-0.02, 1.30); ax2.set_ylim(-0.02, 1.04)
    ax2.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax2.set_xticklabels(["0", "25", "50", "75", "100%"])
    ax2.set_yticks([0, 0.25, 0.5, 0.75, 1.0]); ax2.set_yticklabels(["0", "25", "50", "75", "100%"])
    ax2.xaxis.grid(True, color=GRID, linewidth=0.7, zorder=0); ax2.yaxis.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.spines["left"].set_color(RULE); ax2.spines["bottom"].set_color(RULE)
    ax2.tick_params(length=0)
    ax2.set_xlabel("corruption flagged in concerns")
    ax2.set_ylabel("corrupted value in final answer")
    ax2.set_title("(b) Noticing vs. answering", loc="left", weight="bold")
    h = [Line2D([], [], marker="o", color=MUTED, ls="", markersize=4.5, label="impossible"),
         Line2D([], [], marker="s", color=MUTED, ls="", markersize=4.5, label="plausible"),
         Line2D([], [], marker="o", markerfacecolor="white", markeredgecolor=MUTED, ls="", markersize=4.5, label="+ verify")]
    ax2.legend(handles=h, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=3, handlelength=0.9, columnspacing=0.7, fontsize=6.4)
    fig.subplots_adjust(wspace=0.36)
    save(fig, "fig_main")


# ------------------------------------------------------------------ Figure 3: sweep small multiples
def fig_sweep():
    factors = W["factors"]
    models = [m for m in MODELS if m in W["models"]]
    arms = ["consistent", "inconsistent"]
    fig, axes = plt.subplots(len(arms), len(models), figsize=(TW, 1.8), sharex=True, sharey=True)
    xs = list(range(len(factors)))
    for r, arm in enumerate(arms):
        for c, m in enumerate(models):
            ax = axes[r][c]
            cells = [W["cells"].get(f"{m}|all|{arm}|{f:g}") for f in factors]
            prop = [x["propagation"]["rate"] for x in cells]
            flag = [x["flag_rate"]["rate"] for x in cells]
            plo = [max(0, x["propagation"]["rate"] - x["propagation"]["ci_lo"]) for x in cells]
            phi = [max(0, x["propagation"]["ci_hi"] - x["propagation"]["rate"]) for x in cells]
            ax.fill_between(xs, prop, [min(p, f) for p, f in zip(prop, flag)], color=CORRUPT, alpha=0.12, lw=0, zorder=1)
            ax.plot(xs, flag, color=MUTED, ls=(0, (3, 2)), lw=1.0, marker="s", ms=2.4, zorder=3, label="flagged in concerns")
            ax.errorbar(xs, prop, yerr=[plo, phi], color=COLOR[m], lw=1.6, marker="o", ms=2.8, elinewidth=0.55, capsize=1.2,
                        zorder=4, label="corrupted value in answer")
            # value labels: propagation where it leaves 100%, plus the most severe point; flagged at the two ends
            for i, (p, f) in enumerate(zip(prop, flag)):
                if p >= 0.985:
                    if i == len(factors) - 1:
                        ax.text(xs[i], p + 0.035, f"{100 * p:.0f}", ha="center", va="bottom", fontsize=5.6, color=COLOR[m], zorder=6)
                elif f < p:
                    ax.text(xs[i], cells[i]["propagation"]["ci_hi"] + 0.03, f"{100 * p:.0f}", ha="center", va="bottom", fontsize=5.6, color=COLOR[m], zorder=6)
                else:
                    ax.text(xs[i], cells[i]["propagation"]["ci_lo"] - 0.03, f"{100 * p:.0f}", ha="center", va="top", fontsize=5.6, color=COLOR[m], zorder=6)
            ax.text(xs[0] - 0.12, flag[0] + 0.05, f"{100 * flag[0]:.0f}", ha="right", va="bottom", fontsize=5.6, color=MUTED, zorder=6)
            style(ax, ylim=(-0.06, 1.16))
            ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
            ax.set_xticks(xs); ax.set_xticklabels([f"{f:g}" for f in factors], fontsize=6.4, rotation=45, ha="right", rotation_mode="anchor")
            if c == 0:
                ax.set_ylabel("record kept\nconsistent" if arm == "consistent" else "record made\ninconsistent", fontsize=7.5)
            if r == 0:
                ax.set_title(LABEL[m], loc="left", weight="bold", color=COLOR[m])
            if r == 1 and c == 1:
                ax.set_xlabel("factor applied to the true length or mass (more severe →)")
    axes[0][0].legend(frameon=False, loc="center left", handlelength=1.4, fontsize=6.2, bbox_to_anchor=(-0.03, 0.45), labelspacing=0.3)
    axes[0][2].text(2.4, 0.22, "at ×0.005 the records have\n1–5 residues and 100–600 Da", fontsize=6, color=MUTED, va="bottom")
    axes[1][1].text(2.5, 0.10, "mass recomputed\nfrom length", fontsize=6, color=MUTED, va="bottom")
    fig.subplots_adjust(hspace=0.16, wspace=0.10)
    save(fig, "fig_sweep")


# ------------------------------------------------------------------ Figure 4 (appendix): heatmaps
def fig_heatmap():
    rows = [(m, c) for m in MODELS for c in CONDS if bc(m, c)]
    fig, axes = plt.subplots(1, 2, figsize=(TW, 2.75), sharey=True)
    fig.subplots_adjust(left=0.27, right=0.99, top=0.92, bottom=0.10, wspace=0.06)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("blues", BLUES)
    for ax, (key, title) in zip(axes, [("propagation", "(a) Propagation"), ("silent_propagation", "(b) Silent propagation")]):
        for i, (m, c) in enumerate(rows):
            for j, f in enumerate(FIELDS):
                a = S["by_model_condition_field"][m].get(f"{c}|{f}")
                v = a[key]["rate"] if a else float("nan")
                ax.add_patch(Rectangle((j, i), 1, 1, fc=cmap(v) if not math.isnan(v) else "white", ec="white", lw=1.2))
                if a:
                    ax.text(j + 0.5, i + 0.5, f"{100 * v:.0f}%  ({a[key]['k']}/{a[key]['n']})", ha="center", va="center",
                            fontsize=5.7, color="white" if v > 0.55 else INK)
        for gi in range(1, len(MODELS)):
            ax.axhline(4 * gi, color=INK, lw=0.8)
        ax.set_xlim(0, 4); ax.set_ylim(len(rows), 0)
        ax.set_xticks([j + 0.5 for j in range(4)]); ax.set_xticklabels([f.replace("_", " ") for f in FIELDS], fontsize=7)
        ax.xaxis.tick_top(); ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(title, loc="left", weight="bold", pad=16)
    axes[0].set_yticks([i + 0.5 for i in range(len(rows))])
    axes[0].set_yticklabels([f"{LABEL[m]} · {c.replace('+verify', ' + verify')}" for m, c in rows], fontsize=6.4)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=matplotlib.colors.Normalize(0, 1))
    cax = fig.add_axes([0.45, 0.035, 0.36, 0.014])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_ticks([0, 0.5, 1]); cb.set_ticklabels(["0", "50", "100%"]); cb.outline.set_visible(False)
    cax.tick_params(length=0, labelsize=6.5)
    save(fig, "fig_heatmap")


def fig_cues():
    """Cue composition of flagged concerns: one panel per corruption group, grouped bars per model."""
    A = json.loads((OUT.parent / "analysis.json").read_text())["taxonomy"]
    groups = ["impossible", "plausible", "sweep consistent", "sweep inconsistent"]
    cues = [("crossfield", "cross-field", "#2a78d6"), ("recall", "recall", "#eb6834"), ("rule", "rule", "#1baf7a"), ("none", "unspecific", "#9a9891")]
    fig, axes = plt.subplots(1, 4, figsize=(TW, 1.75), sharey=True)
    for ax, g in zip(axes, groups):
        ms = [m for m in MODELS if f"{g}|{m}" in A and A[f"{g}|{m}"]["n_flagged"]]
        w = 0.8 / len(cues)
        for j, (key, lab, col) in enumerate(cues):
            xs = [i - 0.4 + w * (j + 0.5) for i in range(len(ms))]
            ys = [A[f"{g}|{m}"][key] for m in ms]
            ax.bar(xs, ys, width=w * 0.92, color=col, edgecolor="white", linewidth=0.4, label=lab, zorder=3)
            for x, y in zip(xs, ys):
                ax.text(x, y + 0.02, f"{100 * y:.0f}", ha="center", va="bottom", fontsize=4.8, color=INK, rotation=90, zorder=5)
        ax.set_xticks(range(len(ms))); ax.set_xticklabels([LABEL[m].replace(" ", "\n") for m in ms], fontsize=5.8)
        style(ax, ylim=(0, 1.22))
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
        ax.set_title(f"{g.replace('sweep ', 'sweep, ')}\n(n = {sum(A[f'{g}|{m}']['n_flagged'] for m in ms)} flagged runs)", loc="left", fontsize=6.8, weight="bold")
    axes[0].set_ylabel("share of flagged runs")
    axes[-1].legend(frameon=False, fontsize=6.2, loc="upper left", bbox_to_anchor=(1.0, 1.0), handlelength=0.9, labelspacing=0.3)
    fig.subplots_adjust(wspace=0.12)
    save(fig, "fig_cues")


def numbers():
    out = {"models": {}, "sweep": {}, "total_runs": S["n_runs"] + len(W["runs"]),
           "cost_main": S["cost_usd"], "cost_sweep": sum(r["cost_usd"] for r in W["runs"])}
    for m in MODELS:
        out["models"][m] = {c: {k: S["by_model_condition"][m][c][k] for k in ("accuracy", "propagation", "flag_rate", "silent_propagation", "recall_rate", "mean_tool_calls", "n")}
                            for c in S["by_model_condition"][m]}
    for m in W["models"]:
        for arm in ("consistent", "inconsistent"):
            out["sweep"][f"{m}|{arm}"] = {f"{f:g}": {k: W["cells"][f"{m}|all|{arm}|{f:g}"][k] for k in ("propagation", "flag_rate")} for f in W["factors"]}
    (OUT.parent / "numbers.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    fig_design(); fig_main(); fig_sweep(); fig_heatmap(); fig_cues(); numbers()
    print("figures:", sorted(p.name for p in OUT.iterdir() if p.suffix == ".pdf"))
