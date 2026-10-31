"""NMI figures 1, 4, 5 and 6 from the committed result files. Run from the repository root: python paper/make_figures_nmi.py"""
import json, math, os, sys
sys.path.insert(0, os.getcwd())
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
OUT = "paper/figures"; os.makedirs(OUT, exist_ok=True)
COL = {"opus5": "#b4700a", "argon": "#1c5cab", "flash": "#6da7ec", "deepseek": "#7b4fb3", "sonnet5": "#e07b39"}
NAME = {"opus5": "Opus 5", "argon": "Gemini 4 Argon", "flash": "Gemini 3.8 Flash", "deepseek": "DeepSeek V4.1 Flash", "sonnet5": "Sonnet 5"}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})
def wilson(k, n, z=1.96):
    if n == 0: return math.nan, math.nan, math.nan
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h
def rows(path, cond=None):
    if not os.path.exists(path): return []
    seen = {}
    for l in open(path):
        t = json.loads(l); seen[t["run_key"]] = t
    ok = [t for t in seen.values() if not (t.get("trace") or {}).get("error") and (t.get("trace") or {}).get("parsed_ok", True)]
    return [t for t in ok if cond is None or t["condition"] == cond]
def kn(ts): return sum(bool(t.get("propagated")) for t in ts), len(ts)
def grouped(ax, groups, series, labels, colors, alphas=None):
    w = 0.8 / len(series)
    for j, ser in enumerate(series):
        xs = [i + (j - (len(series) - 1) / 2) * w for i in range(len(groups))]
        st = [wilson(*kn_) for kn_ in ser]
        ys = [100 * p for p, _, _ in st]; err = [[100 * (p - a) for p, a, _ in st], [100 * (b - p) for p, _, b in st]]
        ax.bar(xs, ys, w, color=colors[j], alpha=(alphas[j] if alphas else 1.0), edgecolor="black", linewidth=0.4, label=labels[j])
        ax.errorbar(xs, ys, yerr=err, fmt="none", ecolor="black", elinewidth=0.6, capsize=1.5)
    ax.set_xticks(range(len(groups))); ax.set_ylim(0, 105)
def fig_deployment():
    D = {"deepseek": {"impossible": (5, 287), "plausible": (80, 285)}, "flash": {"impossible": (6, 286), "plausible": (69, 288)}}
    # src: results/biomni_full_deepseek and results/biomni_full_flash analyses (delivered corrupted runs)
    fig, ax = plt.subplots(figsize=(3.4, 2.4)); M = list(D)
    grouped(ax, M, [[D[m]["impossible"] for m in M], [D[m]["plausible"] for m in M]], ["impossible value", "plausible value"], ["#bbbbbb", "#555555"])
    ax.set_xticklabels([NAME[m] for m in M]); ax.set_ylabel("Corrupted value relayed (%)"); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(f"{OUT}/nmi_deployment.pdf"); plt.close(fig)
def fig_agreement():
    M = ["opus5", "argon", "flash", "deepseek"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True)
    for ax, title, arms in ((axes[0], "a  Molecular weight asked", ("B", "C")), (axes[1], "b  Monoisotopic mass asked", ("P4", "A"))):
        w = 0.38
        for j, arm in enumerate(arms):
            st = [wilson(*kn(rows(f"results/robustness/{m}_4b_{arm}.jsonl", "plausible"))) for m in M]
            xs = [i + (j - 0.5) * w for i in range(len(M))]; ys = [100 * p for p, _, _ in st]
            ax.bar(xs, ys, w, color=[COL[m] for m in M], alpha=1.0 if j == 0 else 0.45, edgecolor="black", linewidth=0.4)
            ax.errorbar(xs, ys, yerr=[[100 * (p - a) for p, a, _ in st], [100 * (b - p) for p, _, b in st]], fmt="none", ecolor="black", elinewidth=0.6, capsize=1.5)
        ax.set_xticks(range(len(M))); ax.set_xticklabels([NAME[m] for m in M], rotation=20, ha="right"); ax.set_ylim(0, 105); ax.set_title(title, loc="left")
    axes[0].legend(handles=[Patch(facecolor="grey", edgecolor="black", label="weight + heavy atoms agree"), Patch(facecolor="grey", alpha=0.45, edgecolor="black", label="+ monoisotopic mass agrees")], frameon=False, loc="lower right", fontsize=7)
    axes[1].legend(handles=[Patch(facecolor="grey", edgecolor="black", label="weight + heavy atoms agree"), Patch(facecolor="grey", alpha=0.45, edgecolor="black", label="mass corrupted alone")], frameon=False, loc="lower right", fontsize=7)
    axes[0].set_ylabel("Wrong value relayed (%)"); fig.tight_layout(); fig.savefig(f"{OUT}/nmi_agreement.pdf"); plt.close(fig)
def fig_real_errors():
    M = ["opus5", "argon", "deepseek"]; T = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))
    grouped(axes[0], M, [[kn(rows(f"results/phase5/{m}_{f}.jsonl", "superseded")) for m in M] for f in ("full", "summary")], ["full record", "summary record"], ["#555555", "#bbbbbb"])
    axes[0].set_xticklabels([NAME[m] for m in M]); axes[0].set_ylabel("Superseded value relayed (%)"); axes[0].legend(frameon=False, loc="lower right"); axes[0].set_title("a", loc="left")
    bins = (("1-5", 1, 5), ("6-50", 6, 50), (">50", 51, 10 ** 6))
    def inbin(t, lo, hi): return lo <= abs(T[t["task_id"]]["corruptions"]["superseded"]["d_length"]) <= hi
    full = {m: rows(f"results/phase5/{m}_full.jsonl", "superseded") for m in M}
    grouped(axes[1], [b[0] for b in bins], [[kn([t for t in full[m] if inbin(t, lo, hi)]) for _, lo, hi in bins] for m in M], [NAME[m] for m in M], [COL[m] for m in M])
    axes[1].set_xticklabels([f"{b[0]} residues" for b in bins]); axes[1].legend(frameon=False, loc="lower right", fontsize=7); axes[1].set_title("b", loc="left")
    fig.tight_layout(); fig.savefig(f"{OUT}/nmi_real_errors.pdf"); plt.close(fig)
def fig_presentation():
    from harness import second_source as ss
    M = ["opus5", "argon", "deepseek"]; T = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
    arms = (("p5_annotate", "annotate"), ("p5_replace", "replace,\nambiguous labels"), ("p5_replace_labeled", "replace,\nlabelled original"), ("p5_replace_silent", "replace,\nsilent"))
    cov = lambda t: bool(ss._AF.get(T[t["task_id"]]["target_accession"]))
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    grouped(ax, [a[1] for a in arms], [[kn([t for t in rows(f"results/robustness/{m}_{a}.jsonl", "superseded") if cov(t)]) for a, _ in arms] for m in M], [NAME[m] for m in M], [COL[m] for m in M])
    ax.set_xticklabels([a[1] for a in arms]); ax.set_ylim(0, 50); ax.set_ylabel("Superseded value relayed (%)"); ax.legend(frameon=False, loc="upper right")
    fig.tight_layout(); fig.savefig(f"{OUT}/nmi_presentation.pdf"); plt.close(fig)
for f in (fig_deployment, fig_agreement, fig_real_errors, fig_presentation): f(); print("wrote", f.__name__)
