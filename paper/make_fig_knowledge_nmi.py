"""Figure 'What the agent brings to a contradiction': identity, reasoning, unprompted doubt, Biomni computing. Computed from the run files."""
import json, os, re, glob, math, ast
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"], "font.size": 7, "axes.labelsize": 7,
                     "xtick.labelsize": 6.2, "ytick.labelsize": 6.5, "legend.fontsize": 6.2, "axes.linewidth": 0.6, "pdf.fonttype": 42})
COL = {"opus5": "#B8860B", "argon": "#1F4E9C", "flash": "#6FA3E0", "deepseek": "#7B3FA0", "sonnet5": "#E0803C"}
try:
    m = re.search(r"\nCOL\s*=\s*(\{[^\n]*\})", open("paper/make_figures_nmi.py").read())
    if m: COL.update(ast.literal_eval(m.group(1)))
except Exception: pass
COL.setdefault("sonnet5", "#E0803C")
NAME = {"opus5": "Opus 5", "argon": "Gemini 4 Argon", "deepseek": "DeepSeek V4.1 Flash", "sonnet5": "Sonnet 5", "flash": "Gemini 3.8 Flash"}
def rows(p):
    if not os.path.exists(p): return []
    d = {}
    for l in open(p):
        try: r = json.loads(l)
        except Exception: continue
        d[r.get("run_key", len(d))] = r
    return [r for r in d.values() if not (r.get("trace") or {}).get("error") and (r.get("trace") or {}).get("parsed_ok", True)]
def kn(rs, cond, what="propagated"):
    c = [r for r in rs if r.get("condition") == cond]; return sum(bool(r.get(what)) for r in c), len(c)
def bench(r): return (r.get("prompt_variant") or "default") == "default" and not r.get("verify_prompt") and r.get("harness") in (None, "none", False) and str(r.get("sample", 0)) == "0" and r.get("record_format") in (None, "summary")
def wilson(k, n, z=1.96):
    if not n: return (float("nan"),) * 3
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * p, 100 * min(p, c - h), 100 * max(p, c + h)
def point(ax, x, k, n, color, filled=True, marker="o", ms=3.4):
    y, lo, hi = wilson(k, n)
    ax.errorbar([x], [y], yerr=[[y - lo], [hi - y]], fmt=marker, color=color, mfc=color if filled else "white", ms=ms, elinewidth=0.6, capsize=1.5)
    return y
def style(ax, letter, title, xs, labels, ylabel=None, top=103):
    ax.set_xticks(xs); ax.set_xticklabels(labels); ax.set_ylim(-3, top); ax.set_xlim(xs[0] - 0.6, xs[-1] + 0.6)
    ax.set_yticks([0, 25, 50, 75, 100]); ax.grid(axis="y", lw=0.4, alpha=0.4)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.text(-0.02 if len(xs) > 4 else -0.16, 1.05, letter, transform=ax.transAxes, fontweight="bold", fontsize=9, va="bottom", ha="right" if len(xs) > 4 else "left")
    ax.set_title(title, loc="left", fontsize=7.2, pad=3)
    if ylabel: ax.set_ylabel(ylabel)
fig = plt.figure(figsize=(6.5, 5.6)); gs = fig.add_gridspec(2, 3)
axa, axb, axc, axd = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1:]), fig.add_subplot(gs[1, :2]), fig.add_subplot(gs[1, 2])
OFF = {"opus5": -0.15, "argon": 0.0, "deepseek": 0.15}
for m in ("opus5", "argon", "deepseek"):
    A = [rows(f"results/round2/{m}_IS_identity.jsonl"), rows(f"results/round2/{m}_IS_minimal.jsonl"), [r for r in rows(f"results/round2/{m}_IS_bench.jsonl") if str(r.get("sample", 0)) == "0"]]
    ys = [point(axa, i + OFF[m], *kn(rs, "plausible"), COL[m]) for i, rs in enumerate(A)]
    axa.plot([i + OFF[m] for i in range(3)], ys, color=COL[m], lw=0.8)
style(axa, "a", "Identity", [0, 1, 2], ["full\nrecord", "identity,\nno annot.", "neither"], "Wrong value relayed (%)")
axa.legend(handles=[Line2D([], [], marker="o", color=COL[m], ms=3.4, lw=0.8, label=NAME[m]) for m in ("opus5", "argon", "deepseek")], loc="center left", frameon=False)
O_th = rows("results/round2/opus5_TH_full.jsonl"); ot = {r["task_id"] for r in O_th}
O_on = [r for r in rows("results/v2_full/traces_opus5.jsonl") if (r.get("prompt_variant") or "default") == "default" and r.get("harness") in (None, "none", False) and r["task_id"] in ot]
S = {}
for dom, bp in (("protein", "results/v2/traces_sonnet5.jsonl"), ("chem", "results/chem/traces_sonnet5.jsonl")):
    th = rows(f"results/round2/sonnet5_TH_{dom}.jsonl"); tt = {r["task_id"] for r in th}; S[dom] = ([r for r in rows(bp) if bench(r) and r["task_id"] in tt], th)
CATS = [("full\nplaus.", "opus5", O_on, O_th, "plausible"), ("full\nimposs.", "opus5", O_on, O_th, "impossible"),
        ("protein\nimposs.", "sonnet5", *S["protein"], "impossible"), ("protein\nplaus.", "sonnet5", *S["protein"], "plausible"),
        ("chem.\nimposs.", "sonnet5", *S["chem"], "impossible"), ("chem.\nplaus.", "sonnet5", *S["chem"], "plausible")]
for i, (lab, m, on, off, cond) in enumerate(CATS):
    y1 = point(axb, i - 0.12, *kn(on, cond), COL[m]); y2 = point(axb, i + 0.12, *kn(off, cond), COL[m], filled=False); axb.plot([i - 0.12, i + 0.12], [y1, y2], color=COL[m], lw=0.7)
style(axb, "b", "Reasoning: thinking on (filled) or off (open)", list(range(6)), [c[0] for c in CATS])
axb.legend(handles=[Line2D([], [], marker="o", color=COL["opus5"], ls="", ms=3.4, label="Opus 5, full record"), Line2D([], [], marker="o", color=COL["sonnet5"], ls="", ms=3.4, label="Sonnet 5, summary record")], loc="lower right", frameon=False)
J = json.load(open("results/round2/nc_judge.json")); labs, i = [], 0
for g, m in enumerate(("opus5", "argon", "deepseek")):
    for dom in ("protein", "chem"):
        for cond in ("impossible", "plausible"):
            d = J[f"{m}_{dom}_{cond}"]
            y1 = point(axc, i - 0.13, *d["solicited"], COL[m], marker="s", ms=3.0); y2 = point(axc, i + 0.13, *d["judge_no_concerns"], COL[m], filled=False)
            axc.plot([i - 0.13, i + 0.13], [y1, y2], color=COL[m], lw=0.7); labs.append(("prot." if dom == "protein" else "chem.") + "\n" + ("imp." if cond == "impossible" else "plaus.")); i += 1
    axc.text(4 * g + 1.5, 108, NAME[m], ha="center", va="bottom", fontsize=6.4, color=COL[m])
    if g: axc.axvline(4 * g - 0.5, color="0.85", lw=0.6)
style(axc, "c", "Doubt voiced when asked to list concerns (squares) and when not asked (circles)", list(range(12)), labs, "Runs voicing doubt (%)", top=116)
LEN = re.compile(r"len\(\s*[\w\.\[\]'\"]*seq|ProteinAnalysis|molecular_weight\(|calculate.{0,20}(mass|weight)|count.{0,20}residue", re.I)
G = {(r["task"], r["cond"]): r for r in json.load(open("results/biomni_rerun/flash/graded.json"))}; comp = {}
for f in glob.glob("results/biomni_rerun/flash/out_*.json"):
    o = json.load(open(f)); t = o.get("final") or ""
    comp[(str(o.get("task_id")), str(o.get("condition")))] = bool(LEN.search(" ".join(re.findall(r"<execute>(.*?)(?=<execute>|<observ|<solution>|$)", t, flags=re.S))))
for i, fld in enumerate(("length", "mass")):
    D = [r for r in G.values() if r["cond"] == "plausible" and r["delivered"] and r["parsed"] and r["field"] == fld]
    c = [r for r in D if comp.get((r["task"], "plausible"))]; n_ = [r for r in D if not comp.get((r["task"], "plausible"))]
    y1 = point(axd, i - 0.12, sum(bool(r["propagated"]) for r in c), len(c), COL["flash"]); y2 = point(axd, i + 0.12, sum(bool(r["propagated"]) for r in n_), len(n_), COL["flash"], filled=False)
    axd.plot([i - 0.12, i + 0.12], [y1, y2], color=COL["flash"], lw=0.7)
style(axd, "d", "Biomni, Gemini 3.8 Flash", [0, 1], ["length", "mass"])
axd.legend(handles=[Line2D([], [], marker="o", color=COL["flash"], ls="", ms=3.4, label="computed from sequence"), Line2D([], [], marker="o", color=COL["flash"], mfc="white", ls="", ms=3.4, label="did not compute")], loc="lower right", frameon=False)
fig.tight_layout(w_pad=1.0, h_pad=1.4); fig.savefig("paper/figures/nmi_knowledge.pdf"); print("wrote paper/figures/nmi_knowledge.pdf")
