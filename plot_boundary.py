import json, math, re, glob, sys
from collections import defaultdict
sys.path.insert(0, "."); sys.path.insert(0, "paper")
from analysis import load_runs, score
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ORDER = ["opus5", "argon", "flash", "deepseek", "sonnet5"]
LABEL = {"opus5": "Opus 5", "argon": "Gemini 4 Argon", "flash": "Gemini 3.8 Flash", "deepseek": "DeepSeek V4.1 Flash", "sonnet5": "Sonnet 5"}
COLOR = {"opus5": "#b4700a", "argon": "#1c5cab", "flash": "#6da7ec", "deepseek": "#7b4fb3", "sonnet5": "#e07b39"}
rows = defaultdict(lambda: defaultdict(list))
for f in sorted(glob.glob("results/boundary/traces_*.jsonl")):
    m, dom, d = re.match(r".*/traces_(\w+?)_(protein|chem)_(shrink|inflate)\.jsonl", f).groups()
    for r in load_runs([f]):
        s = score(r)
        if s["base_condition"] != "clean": rows[(m, dom, d)][float(s["base_condition"][1:].split("_")[0])].append(bool(s["propagated"]))
plt.rcParams.update({"font.family": "serif", "font.size": 7.5, "axes.titlesize": 8, "legend.fontsize": 6.5, "pdf.fonttype": 42})
fig, axes = plt.subplots(1, 4, figsize=(6.75, 2.2), sharey=True, gridspec_kw={"wspace": 0.12})
panels = [("protein", "shrink", "(a) proteins, value decreased"), ("protein", "inflate", "(b) proteins, value increased"),
          ("chem", "shrink", "(c) molecules, value decreased"), ("chem", "inflate", "(d) molecules, value increased")]
out = {}
for ax, (dom, d, title) in zip(axes, panels):
    for m in ORDER:
        cur = rows.get((m, dom, d))
        if not cur: continue
        facs = sorted(cur, reverse=(d == "shrink")); ys = [np.mean(cur[f]) for f in facs]; xs = [abs(math.log10(f)) for f in facs]
        ax.plot(xs, ys, "-o", color=COLOR[m], lw=1.1, ms=3, label=LABEL[m], zorder=3)
        out[f"{m}|{dom}|{d}"] = {f"{f:g}": float(y) for f, y in zip(facs, ys)}
    ax.axhline(0.5, color="#c3c2b7", lw=0.6, ls="--", zorder=1)
    ax.set_xticks([abs(math.log10(f)) for f in ([0.9, 0.7, 0.5, 0.3, 0.1, 0.02, 0.005] if d == "shrink" else [1.1, 1.5, 2, 3, 10, 50, 200])])
    ax.set_xticklabels([f"×{f:g}" for f in ([0.9, 0.7, 0.5, 0.3, 0.1, 0.02, 0.005] if d == "shrink" else [1.1, 1.5, 2, 3, 10, 50, 200])], rotation=45, ha="right")
    ax.set_title(title, loc="left", weight="bold"); ax.set_ylim(-0.02, 1.05); ax.set_yticks([0, .25, .5, .75, 1]); ax.set_yticklabels(["0", "25", "50", "75", "100%"])
    ax.yaxis.grid(True, color="#e6e5e1", lw=0.6); [ax.spines[s].set_visible(False) for s in ("top", "right", "left")]; ax.tick_params(length=0)
    ax.set_xlabel("corruption factor (full record)")
axes[0].set_ylabel("corrupted value in final answer")
fig.legend(handles=axes[0].get_legend_handles_labels()[0], labels=axes[0].get_legend_handles_labels()[1], loc="lower center", bbox_to_anchor=(0.5, -0.2), ncol=5, frameon=False, handlelength=1.0)
fig.savefig("paper/figures/icml_boundary.pdf", bbox_inches="tight", pad_inches=0.02); fig.savefig("paper/figures/icml_boundary.png", bbox_inches="tight", dpi=250)
json.dump(out, open("results/boundary/curves.json", "w"), indent=1); print("wrote paper/figures/icml_boundary.pdf and results/boundary/curves.json")
