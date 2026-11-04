"""Fig. 7, what turns detection into override. Counts are relayed/parsed runs from
results/analysis/analyze_new_experiments.py (prompt ablation, repetition, withholding harness)
and results/memory_probe/analysis.json (memory probe), repository state afdfce6."""
import ast, math, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
                     "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                     "legend.fontsize": 6.2, "axes.linewidth": 0.6, "pdf.fonttype": 42})
COL = {"opus5": "#B8860B", "argon": "#1F4E9C", "flash": "#6FA3E0", "deepseek": "#7B3FA0"}
try:  # reuse the main figure script's palette when it can be read
    m = re.search(r"\nCOL\s*=\s*(\{[^\n]*\})", open("paper/make_figures_nmi.py").read())
    if m: COL.update(ast.literal_eval(m.group(1)))
except Exception: pass
NAME = {"opus5": "Opus 5", "argon": "Gemini 4 Argon", "flash": "Gemini 3.8 Flash", "deepseek": "DeepSeek V4.1 Flash"}
OFF = {"opus5": -0.21, "argon": -0.07, "flash": 0.07, "deepseek": 0.21}

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * p, 100 * (c - h), 100 * (c + h)

# a-c, prompt variants: [default, no tool instruction, database has errors, two fields]
PROMPT = {
 "a": {"opus5": [(9, 49), (4, 49), (0, 38), (5, 47)], "argon": [(7, 50), (6, 50), (1, 50), (0, 50)], "deepseek": [(50, 50), (42, 49), (23, 42), (34, 47)]},
 "b": {"opus5": [(163, 180), (85, 180), (0, 180), (0, 180)], "argon": [(144, 180), (92, 180), (0, 180), (0, 180)],
       "flash": [(159, 174), (58, 171), (0, 180), (6, 163)], "deepseek": [(152, 180), (140, 180), (2, 180), (19, 180)]},
 "c": {"opus5": [(49, 50), (48, 50), (50, 50), (26, 50)], "argon": [(48, 50), (47, 50), (50, 50), (0, 50)], "deepseek": [(47, 50), (46, 50), (49, 49), (45, 50)]}}
# d, repetition: [R0 weight alone, R1 repeat agrees, R2 repeat disagrees, B derived field agrees]
REP = {"opus5": [(102, 180), (66, 180), (0, 180), (113, 180)], "argon": [(117, 180), (67, 180), (3, 180), (130, 180)],
       "flash": [(152, 177), (135, 178), (1, 180), (154, 175)], "deepseek": [(115, 180), (105, 179), (5, 180), (128, 180)]}
# e, memory probe: (current-memory, superseded-memory) proteins, without (full record) and with the second source
MEM = {"opus5": {"without": [(47, 48), (7, 7)], "with": [(2, 144), (13, 21)]},
       "argon": {"without": [(48, 53), (6, 6)], "with": [(4, 159), (0, 17)]},
       "deepseek": {"without": [(50, 50), (6, 6)], "with": [(38, 150), (17, 18)]}}
# f, withholding harness: (numeric fields, identifiers), impossible and plausible pooled
BLANK = {"opus5": {"proteins": [(0, 91), (0, 100)], "molecules": [(0, 150), (8, 50)]},
         "argon": {"proteins": [(0, 97), (0, 100)], "molecules": [(0, 150), (5, 50)]},
         "deepseek": {"proteins": [(0, 71), (5, 100)], "molecules": [(0, 150), (23, 50)]}}

def series(ax, data, xs):
    for m, pts in data.items():
        ys = [wilson(k, n) for k, n in pts]
        ax.errorbar([x + OFF[m] for x in xs], [y[0] for y in ys], yerr=[[y[0] - y[1] for y in ys], [y[2] - y[0] for y in ys]],
                    fmt="o-", color=COL[m], ms=3.2, lw=0.9, elinewidth=0.6, capsize=1.5, label=NAME[m])

def point(ax, x, k, n, color, marker="o", filled=True, ms=3.3):
    y, lo, hi = wilson(k, n)
    ax.errorbar([x], [y], yerr=[[y - lo], [hi - y]], fmt=marker, color=color, mfc=color if filled else "white", ms=ms, elinewidth=0.6, capsize=1.5)

def style(ax, letter, title, xs, labels, ylabel=None):
    ax.set_xticks(xs); ax.set_xticklabels(labels); ax.set_ylim(-3, 103); ax.set_xlim(xs[0] - 0.6, xs[-1] + 0.6)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.grid(axis="y", lw=0.4, alpha=0.4)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.text(-0.16, 1.05, letter, transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom")
    ax.set_title(title, loc="left", fontsize=7.2, pad=3)
    if ylabel: ax.set_ylabel(ylabel)

fig, axes = plt.subplots(2, 3, figsize=(6.5, 5.3))
V = ["default", "no tool\ninstruction", "database\nhas errors", "two\nfields"]
for ax, cell, title in zip(axes[0], "abc", ["Proteins, sequence contradicts value", "Molecules, three fields agree", "Coherent protein errors"]):
    series(ax, PROMPT[cell], [0, 1, 2, 3]); style(ax, cell, title, [0, 1, 2, 3], V, "Wrong value relayed (%)" if cell == "a" else None)
axes[0][1].legend(loc="center right", frameon=False, handlelength=1.6)

ax = axes[1][0]; series(ax, REP, [0, 1, 2, 3])
style(ax, "d", "Repetition versus consistency", [0, 1, 2, 3], ["weight\nalone", "repeat\nagrees", "repeat\ndisagrees", "derived\nfield agrees"], "Wrong value relayed (%)")

ax = axes[1][1]
for m, d in MEM.items():
    for gi, g in enumerate(("without", "with")):
        for si in (0, 1):
            point(ax, gi + OFF[m] + (-0.045 if si == 0 else 0.045), *d[g][si], COL[m], filled=(si == 0))
style(ax, "e", "Memory probe: relay by memory state", [0, 1], ["no second\nsource", "second source\nshown"])
ax.legend(handles=[Line2D([], [], marker="o", color="0.3", mfc="0.3", ls="", ms=3.3, label="memory holds current value"),
                   Line2D([], [], marker="o", color="0.3", mfc="white", ls="", ms=3.3, label="memory holds superseded value")], loc="center left", frameon=False)

ax = axes[1][2]
for m, d in BLANK.items():
    for gi, g in enumerate(("proteins", "molecules")):
        for si in (0, 1):
            point(ax, gi + OFF[m] + (-0.045 if si == 0 else 0.045), *d[g][si], COL[m], marker="o" if si == 0 else "D", ms=3.3 if si == 0 else 2.8)
style(ax, "f", "Withholding harness", [0, 1], ["proteins", "molecules"])
ax.legend(handles=[Line2D([], [], marker="o", color="0.3", ls="", ms=3.3, label="numeric field (withheld if mismatched)"),
                   Line2D([], [], marker="D", color="0.3", ls="", ms=2.8, label="identifier (not checked)")], loc="upper left", frameon=False)
fig.tight_layout(w_pad=1.2, h_pad=1.6); fig.savefig("paper/figures/nmi_mechanism.pdf"); print("wrote paper/figures/nmi_mechanism.pdf")
