#!/usr/bin/env python3
"""NMI figure set: Figs 1, 3, 4, 5, 6 (Fig. 2 comes from make_figures_icml.py), drawn at print width (6.5 in) in the ICML style.
Run from the repository root: python paper/make_figures_nmi.py"""
import collections, glob, json, math, os, re, sys
sys.path.insert(0, os.getcwd())
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch
from matplotlib.ticker import NullLocator
import numpy as np

OUT = "paper/figures"; os.makedirs(OUT, exist_ok=True)
INK, MUTED, RULE, GRID = "#1f1f1f", "#6b6b6b", "#b8b8b8", "#ececec"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
    "font.size": 7.5, "axes.titlesize": 7.6, "axes.labelsize": 7.2, "xtick.labelsize": 6.6, "ytick.labelsize": 6.6,
    "legend.fontsize": 6.5, "axes.edgecolor": RULE, "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.5, "axes.axisbelow": True, "pdf.fonttype": 42, "ps.fonttype": 42})
TW = 6.5
COL = {"opus5": "#b4700a", "sonnet5": "#e07b39", "argon": "#1c5cab", "flash": "#6da7ec", "deepseek": "#7b4fb3"}
NAME = {"opus5": "Opus 5", "sonnet5": "Sonnet 5", "argon": "Gemini 4 Argon", "flash": "Gemini 3.8 Flash", "deepseek": "DeepSeek V4.1 Flash"}
SHORT = {"opus5": "Opus 5", "sonnet5": "Sonnet 5", "argon": "Argon", "flash": "Flash", "deepseek": "DeepSeek"}
LONGER, SHORTER = "#c0392b", "#2471a3"

def wilson(k, n, z=1.96):
    if n == 0: return math.nan, math.nan, math.nan
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h
def pct(k, n):
    p, lo, hi = wilson(k, n); return 100 * p, 100 * (p - lo), 100 * (hi - p)
def load(path, cond=None):
    if not os.path.exists(path): return []
    seen = {}
    for i, l in enumerate(open(path)):
        t = json.loads(l); seen[t.get("run_key", i)] = t
    ok = [t for t in seen.values() if not (t.get("trace") or {}).get("error") and (t.get("trace") or {}).get("parsed_ok", True)]
    return [t for t in ok if cond is None or t.get("condition") == cond]
def kn(ts): return sum(bool(t.get("propagated")) for t in ts), len(ts)
def flagged(t): return bool((t.get("trace") or {}).get("concerns"))
def letter(ax, s):
    ax.annotate(s, xy=(0, 1), xycoords="axes fraction", xytext=(-15, 6), textcoords="offset points", fontsize=9.5, weight="bold", va="bottom", ha="left")
def flegend(fig, handles, ncol):
    try: fig.legend(handles=handles, loc="outside upper center", ncol=ncol, frameon=False)
    except ValueError: fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=ncol, frameon=False)
def samples(ax, x, rs, color):
    for s in (0, 1, 2):
        ss = [t for t in rs if int(t.get("sample") or 0) == s]
        if ss: ax.scatter([x + (s - 1) * 0.045], [100 * kn(ss)[0] / len(ss)], s=5, color=color, alpha=0.35, lw=0, zorder=3)

# ------------------------------------------------------------------ Fig. 1
def biomni_fields(d):
    p = os.path.join(d, "graded.json")
    if not os.path.exists(p): return None
    def walk(x, ctx):
        if isinstance(x, dict):
            ks = [str(k).lower() for k in x]
            if any("propag" in k or "relay" in k for k in ks) and any("field" in k for k in ks):
                yield {**ctx, **x}; return
            for k, v in x.items():
                c2 = dict(ctx)
                if str(k).lower() in ("clean", "impossible", "plausible"): c2["condition"] = str(k).lower()
                yield from walk(v, c2)
        elif isinstance(x, list):
            for v in x: yield from walk(v, ctx)
    def pick(r, *subs):
        for k, v in r.items():
            if any(sb in str(k).lower() for sb in subs): return v
        return None
    groups = {"length": "protein length, mass", "mass": "protein length, mass", "organism": "protein organism", "gene_symbol": "names",
              "name": "names", "protein_name": "names", "molecular_weight": "chemistry numbers", "heavy_atom_count": "chemistry numbers",
              "h_bond_donors": "chemistry numbers"}
    out = collections.defaultdict(lambda: [0, 0]); raw = collections.defaultdict(lambda: [0, 0])
    for r in walk(json.load(open(p)), {}):
        cond = str(pick(r, "cond") or "").lower(); prop = pick(r, "propag", "relay")
        if "plausible" not in cond or pick(r, "deliver") is False or prop is None: continue
        fk_ = str(pick(r, "field")); raw[fk_][0] += bool(prop); raw[fk_][1] += 1
        grp = groups.get(fk_)
        if grp is None: continue
        out[grp][0] += bool(prop); out[grp][1] += 1
    print(f"{d}: groups {dict(out)}\n    raw fields {dict(raw)}")
    return dict(raw) or None

def fig1():
    fig = plt.figure(figsize=(TW, 5.7), layout="constrained")
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.15], width_ratios=[1.15, 1])
    ax = fig.add_subplot(gs[0, :]); ax.set_xlim(0, 100); ax.set_ylim(0, 52); ax.axis("off"); letter(ax, "a")
    def box(x, y, w, h, title, lines, fc, ec):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h - 2.0, title, ha="center", va="top", fontsize=7.2, weight="bold")
        for i, l in enumerate(lines): ax.text(x + w / 2, y + h - 6.6 - 3.4 * i, l, ha="center", va="top", fontsize=6.3)
    box(1, 34, 19, 16, "Scientific database", ["UniProt (proteins)", "PubChem (compounds)", "UniSave (past versions)"], "#f4f4f4", RULE)
    box(27, 34, 21, 16, "Tool layer or proxy", ["errors injected here:", "impossible, plausible,", "coherent, historical"], "#fdf1e6", "#e0a060")
    box(55, 34, 19, 16, "Agent", ["10 models, 5 developers", "Biomni (deployed)", "summary or full record"], "#eef3fb", "#7a9fd6")
    box(81, 34, 18, 16, "Answer and concerns", ['{"answer": ...,', '"concerns": [...]}', "relayed? flagged?"], "#f4f4f4", RULE)
    for x0, x1 in ((20.6, 26.4), (48.6, 54.4), (74.6, 80.4)):
        ax.annotate("", xy=(x1, 42), xytext=(x0, 42), arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9))
    ax.annotate("", xy=(37.5, 33.4), xytext=(37.5, 29.8), arrowprops=dict(arrowstyle="-|>", color="#2e7d4f", lw=0.9))
    ax.text(37.5, 29.2, "harness: derivation checks; second source (AlphaFold DB, NCI CACTUS);\nannotate, replace or silent correction",
            ha="center", va="top", fontsize=6.0, color="#2e7d4f")
    ax.text(1, 22.8, "Example protein record (illustrative values); coloured values differ from the true record", fontsize=6.6, weight="bold", va="top")
    TRUE = ("228 aa", "25.0 kDa", "228 aa")
    cards = [("true record", TRUE, INK, ""), ("impossible, one field", ("228 aa", "45 Da", "228 aa"), "#c0392b", "contradicts its paired field"),
             ("plausible, paired fields", ("182 aa", "20.0 kDa", "228 aa"), "#d68910", "contradicts only the sequence"),
             ("coherent or historical", ("182 aa", "20.0 kDa", "182 aa"), "#7b4fb3", "contradicts nothing in the record")]
    for i, (h, vals, c, note) in enumerate(cards):
        x = 1 + i * 24.8
        ax.add_patch(FancyBboxPatch((x, 0.8), 23.2, 18.2, boxstyle="round,pad=0.3,rounding_size=1", fc="white", ec=c, lw=0.9))
        ax.text(x + 11.6, 18.2, h, ha="center", va="top", fontsize=6.6, weight="bold", color=c)
        for j, (fname, v) in enumerate(zip(("length", "mass", "sequence"), vals)):
            yy = 14.6 - 3.0 * j; diff = v != TRUE[j]
            ax.text(x + 3.0, yy, fname, ha="left", va="top", fontsize=6.2, color=MUTED)
            ax.text(x + 20.2, yy, v, ha="right", va="top", fontsize=6.2, color=c if diff else INK, weight="bold" if diff else "normal")
        if note: ax.text(x + 11.6, 3.2, note, ha="center", va="center", fontsize=5.8, color=MUTED, style="italic")
    axb = fig.add_subplot(gs[1, 0]); letter(axb, "b")
    RUNS = [("DeepSeek", "impossible", 300, 287, 5), ("DeepSeek", "plausible", 300, 285, 80),
            ("Flash", "impossible", 300, 286, 6), ("Flash", "plausible", 300, 288, 69)]  # src: results/biomni_full_* (H1 analysis)
    for i, (m, c, n, dlv, rel) in enumerate(RUNS):
        y = len(RUNS) - 1 - i
        axb.barh(y, 100 * rel / n, color="#c0392b", height=0.62)
        axb.barh(y, 100 * (dlv - rel) / n, left=100 * rel / n, color="#9fc5a8", height=0.62)
        axb.barh(y, 100 * (n - dlv) / n, left=100 * dlv / n, color="#dcdcdc", height=0.62)
        axb.text(101.5, y, f"{rel}/{dlv}", va="center", fontsize=6.2)
    axb.set_yticks(range(len(RUNS))); axb.set_yticklabels([f"{m}, {c}" for m, c, *_ in reversed(RUNS)])
    axb.set_xlim(0, 113); axb.set_xticks([0, 25, 50, 75, 100]); axb.set_xlabel("Share of corrupted runs (%)")
    axb.set_title("Biomni on live UniProt and PubChem", loc="left"); axb.grid(axis="y", visible=False)
    axb.legend(handles=[Patch(color="#c0392b", label="relayed"), Patch(color="#9fc5a8", label="caught"), Patch(color="#dcdcdc", label="never requested")],
               loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3, frameon=False)
    axc = fig.add_subplot(gs[1, 1]); letter(axc, "c")
    F = {"deepseek": biomni_fields("results/biomni_full_deepseek"), "flash": biomni_fields("results/biomni_full_flash")}
    ROWS = [("length", "length"), ("mass", "mass"), ("organism", "organism"), ("gene_symbol", "gene symbol"),
            ("molecular_weight", "molecular weight"), ("heavy_atom_count", "heavy-atom count"), ("h_bond_donors", "H-bond donors"), ("name", "compound name")]
    EXACT = {"length", "mass", "molecular_weight", "heavy_atom_count", "h_bond_donors"}
    if any(F.values()):
        axc.axhspan(3.5, 7.5, color="#f4f4f4", zorder=0)
        for i, (fk, _) in enumerate(ROWS):
            for j, m in enumerate(("deepseek", "flash")):
                k, n = (F[m] or {}).get(fk, (0, 0))
                if n == 0: continue
                p, el, eh = pct(k, n); y = i + (-0.22 if j == 0 else 0.22); ex = fk in EXACT
                axc.errorbar(p, y, xerr=[[el], [eh]], fmt="o" if ex else "D", color=COL[m], mfc=COL[m] if ex else "white", ms=3.6, capsize=1.4, lw=0.8, zorder=3)
                axc.text(min(p + eh + 2.5, 93), y, f"{k}/{n}", va="center", fontsize=5.6, color=MUTED)
        axc.set_yticks(range(len(ROWS))); axc.set_yticklabels([l for _, l in ROWS]); axc.set_ylim(len(ROWS) - 0.5, -0.5); axc.set_xlim(0, 105)
        axc.grid(axis="y", visible=False); axc.set_xlabel("Plausible value relayed (%)"); axc.set_title("Relay by field, plausible values", loc="left")
        axc.legend(handles=[Line2D([], [], marker="o", ls="", color=COL[m], label=NAME[m]) for m in ("deepseek", "flash")]
                   + [Line2D([], [], marker="o", ls="", color=INK, label="exact derivation route"), Line2D([], [], marker="D", ls="", mfc="white", mec=INK, label="no route")],
                   loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)
    else:
        axc.axis("off"); axc.text(0.5, 0.5, "per-field breakdown not parsed (see console)", ha="center", va="center", color="#c0392b")
    fig.savefig(f"{OUT}/nmi_deployment.pdf"); plt.close(fig)

# ------------------------------------------------------------------ Fig. 3
def parse_fits():
    out, key = {}, None
    for line in open("results/boundary/fits.txt"):
        s = line.strip(); m = re.match(r"^(\w+)\s+(chem|protein)\s+(shrink|inflate)\b", s)
        if m: key = m.groups(); continue
        m2 = re.search(r"50% override at ×([\d.]+)\s+\[×([\d.]+), ×([\d.]+)\]", s)
        if m2 and key: out[key] = tuple(float(v) for v in m2.groups()); key = None
    return out

def fig3():
    data = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for f in glob.glob("results/boundary/traces_*.jsonl"):
        mm = re.match(r".*traces_(.+)_(protein|chem)_(shrink|inflate)\.jsonl$", f)
        if not mm: continue
        for t in load(f):
            fm = re.match(r"f([\d.]+)_", str(t.get("condition", "")))
            if fm:
                x = data[mm.groups()][float(fm.group(1))]; x[0] += bool(t.get("propagated")); x[1] += 1
    fits = parse_fits(); order = ["opus5", "argon", "flash", "deepseek", "sonnet5"]
    spec = {"shrink": ([0.9, 0.5, 0.1, 0.02, 0.005], (1.05, 0.0038)), "inflate": ([1.1, 2, 10, 50, 200], (0.95, 260))}
    titles = {("protein", "shrink"): "Proteins, value decreased", ("protein", "inflate"): "Proteins, value increased",
              ("chem", "shrink"): "Molecules, value decreased", ("chem", "inflate"): "Molecules, value increased"}
    fig = plt.figure(figsize=(TW, 6.6), layout="constrained")
    gs = fig.add_gridspec(4, 2, height_ratios=[3, 1.15, 3, 1.15])
    for r, dom in enumerate(("protein", "chem")):
        for c, d in enumerate(("shrink", "inflate")):
            ticks, xl = spec[d]
            ax = fig.add_subplot(gs[2 * r, c]); sx = fig.add_subplot(gs[2 * r + 1, c], sharex=ax)
            letter(ax, "abcd"[2 * r + c])
            for a_ in (ax, sx): a_.set_xscale("log")
            ax.axhline(50, color=MUTED, lw=0.6, ls="--", zorder=1)
            for m in order:
                pts = data.get((m, dom, d))
                if not pts: continue
                xs = sorted(pts); st = [wilson(*pts[x]) for x in xs]
                ax.fill_between(xs, [100 * lo for _, lo, _ in st], [100 * hi for _, _, hi in st], color=COL[m], alpha=0.12, lw=0)
                ax.plot(xs, [100 * p for p, _, _ in st], "-o", color=COL[m], ms=2.4, lw=1.0, zorder=3)
            for yi, m in enumerate(order):
                fk = fits.get((m, dom, d))
                if not fk: continue
                est, lo, hi = fk
                if min(xl) <= est <= max(xl):
                    lo_, hi_ = max(lo, min(xl)), min(hi, max(xl))
                    sx.errorbar(est, yi, xerr=[[est - lo_], [hi_ - est]], fmt="D", color=COL[m], mec="white", mew=0.5, ms=4, capsize=1.6, lw=0.9)
                else:
                    sx.text(xl[0], yi, f"  ×{est:.2f}, outside tested range", ha="left", va="center", fontsize=5.8, color=COL[m])
            ax.set_xlim(*xl); ax.set_xticks(ticks); ax.set_xticklabels([f"×{t:g}" for t in ticks]); ax.xaxis.set_minor_locator(NullLocator())
            ax.tick_params(axis="x", labelbottom=False); ax.set_ylim(-3, 103); ax.set_title(titles[(dom, d)], loc="left")
            sx.set_ylim(len(order) - 0.5, -0.5); sx.set_yticks(range(len(order)))
            sx.set_yticklabels([SHORT[m] for m in order] if c == 0 else [], fontsize=6.0)
            sx.grid(axis="y", visible=False); sx.tick_params(axis="y", length=0)
            if c == 0:
                ax.set_ylabel("Corrupted value relayed (%)"); sx.set_ylabel("50% point", fontsize=6.4)
    fig.supxlabel("Corruption factor applied to the field and its paired field (full record available)", fontsize=7.2)
    flegend(fig, [Line2D([], [], color=COL[m], marker="o", ms=3, lw=1, label=NAME[m]) for m in order], 5)
    fig.savefig(f"{OUT}/nmi_boundary.pdf"); plt.close(fig)

# ------------------------------------------------------------------ Fig. 4
def fig4():
    fig = plt.figure(figsize=(TW, 5.4), layout="constrained"); gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1])
    axa = fig.add_subplot(gs[0, :]); letter(axa, "a")
    FIELDS = [("monoisotopic_mass", "monoisotopic mass\n(exact route)"), ("tpsa", "TPSA\n(approximate route)"), ("complexity", "PubChem complexity\n(no route)")]
    M5 = ["opus5", "sonnet5", "argon", "flash", "deepseek"]; P4 = {m: load(f"results/phase4/{m}_full.jsonl") for m in M5}
    for gi, (fld, _) in enumerate(FIELDS):
        axa.axvspan(gi * 6 - 0.7, gi * 6 + 4.7, color="#f6f6f6", zorder=0)
        for mi, m in enumerate(M5):
            x = gi * 6 + mi
            sel = lambda cond: [t for t in P4[m] if t.get("target_field") == fld and t.get("condition") == cond]
            cl, pl, im = sel("clean"), sel("plausible"), sel("impossible")
            if not pl: continue
            v = {"cf": 100 * sum(map(flagged, cl)) / max(len(cl), 1), "pf": 100 * sum(map(flagged, pl)) / len(pl),
                 "pr": 100 * kn(pl)[0] / len(pl), "ir": 100 * kn(im)[0] / max(len(im), 1)}
            axa.vlines(x, min(v.values()), max(v.values()), color=COL[m], lw=0.7, alpha=0.45, zorder=2)
            axa.scatter([x - 0.3], [v["cf"]], marker="x", color=MUTED, s=14, lw=0.8, zorder=3)
            axa.scatter([x], [v["pf"]], marker="o", facecolors="white", edgecolors=COL[m], s=26, lw=1.1, zorder=4)
            axa.scatter([x], [v["pr"]], marker="s", color=COL[m], s=22, zorder=5)
            axa.scatter([x + 0.3], [v["ir"]], marker="^", color=COL[m], s=22, alpha=0.5, zorder=4)
    axa.set_xticks([gi * 6 + 2 for gi in range(3)]); axa.set_xticklabels([f for _, f in FIELDS]); axa.set_xlim(-1, 17)
    axa.set_ylim(-4, 104); axa.set_ylabel("Share of runs (%)"); axa.grid(axis="x", visible=False)
    axa.set_title("New chemistry fields with the full record", loc="left")
    kinds = [Line2D([], [], marker="x", ls="", color=MUTED, label="uncorrupted run flagged"),
             Line2D([], [], marker="o", ls="", mfc="white", mec=INK, label="plausible error flagged"),
             Line2D([], [], marker="s", ls="", color=INK, label="plausible error relayed"),
             Line2D([], [], marker="^", ls="", color=INK, alpha=0.5, label="impossible value relayed")]
    axa.legend(handles=kinds + [Patch(color=COL[m], label=NAME[m]) for m in M5], loc="upper left", bbox_to_anchor=(1.005, 1.0), frameon=False)
    M4 = ["opus5", "argon", "flash", "deepseek"]
    for col, (title, (a1, l1), (a2, l2), ch) in enumerate((("Molecular weight asked", ("B", "one agreeing field"), ("C", "two agreeing fields"), "b"),
                                                           ("Monoisotopic mass asked", ("P4", "two agreeing fields"), ("A", "corrupted alone"), "c"))):
        ax = fig.add_subplot(gs[1, col]); letter(ax, ch)
        for i, m in enumerate(M4):
            pts = []
            for j, arm in enumerate((a1, a2)):
                rs = load(f"results/robustness/{m}_4b_{arm}.jsonl", "plausible"); p, el, eh = pct(*kn(rs)); xj = i + (-0.17 if j == 0 else 0.17)
                ax.errorbar(xj, p, yerr=[[el], [eh]], fmt="o" if j == 0 else "s", color=COL[m], mfc="white" if j == 0 else COL[m], ms=4.2, capsize=1.6, lw=0.8, zorder=4)
                samples(ax, xj, rs, COL[m]); pts.append((xj, p, eh))
            ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], color=COL[m], lw=1.0, alpha=0.8, zorder=2)
            ax.text(i, 105.5, f"{pts[1][1] - pts[0][1]:+.0f}", ha="center", fontsize=6.4, color=COL[m], weight="bold")
        ax.set_xticks(range(len(M4))); ax.set_xticklabels([SHORT[m] for m in M4]); ax.set_xlim(-0.6, len(M4) - 0.4)
        ax.set_ylim(40, 109); ax.set_title(title, loc="left"); ax.grid(axis="x", visible=False)
        if col == 0: ax.set_ylabel("Wrong value relayed (%)")
        ax.legend(handles=[Line2D([], [], marker="o", ls="", mfc="white", mec=INK, label=l1), Line2D([], [], marker="s", ls="", color=INK, label=l2),
                           Line2D([], [], marker="o", ls="", color=INK, alpha=0.35, ms=2.5, label="single sample")],
                  loc="lower right" if col == 0 else "lower left", ncol=1, frameon=False)
    fig.savefig(f"{OUT}/nmi_agreement.pdf"); plt.close(fig)

# ------------------------------------------------------------------ Fig. 5
def fig5():
    from harness import second_source as ss
    T = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
    cov = lambda t: bool(ss._AF.get(T[t["task_id"]]["target_accession"]))
    M3 = ["opus5", "argon", "deepseek"]
    fig = plt.figure(figsize=(TW, 5.2), layout="constrained"); gs = fig.add_gridspec(2, 3)
    ax = fig.add_subplot(gs[0, 0]); letter(ax, "a")
    for i, m in enumerate(M3):
        for j, fmt in enumerate(("full", "summary")):
            p, el, eh = pct(*kn(load(f"results/phase5/{m}_{fmt}.jsonl", "superseded"))); xj = i + (-0.15 if j == 0 else 0.15)
            ax.errorbar(xj, p, yerr=[[el], [eh]], fmt="o", color=COL[m], mfc=COL[m] if j == 0 else "white", ms=4.2, capsize=1.6, lw=0.8, zorder=4)
        samples(ax, i - 0.15, load(f"results/robustness/{m}_p5_full.jsonl", "superseded"), COL[m])
    ax.set_xticks(range(3)); ax.set_xticklabels([SHORT[m] for m in M3]); ax.set_ylim(70, 102); ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("Superseded value relayed (%)"); ax.set_title("No second source", loc="left"); ax.grid(axis="x", visible=False)
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=INK, label="full record"), Line2D([], [], marker="o", ls="", mfc="white", mec=INK, label="summary"),
                       Line2D([], [], marker="o", ls="", color=INK, alpha=0.35, ms=2.5, label="repeat sample")], loc="lower left", frameon=False, fontsize=6)
    ax = fig.add_subplot(gs[0, 1:]); letter(ax, "b"); rng = np.random.default_rng(5)
    per = collections.defaultdict(list)
    for m in M3:
        for fmt in ("full", "summary"):
            for t in load(f"results/phase5/{m}_{fmt}.jsonl", "superseded"): per[t["task_id"]].append(bool(t.get("propagated")))
    for tid, v in per.items():
        c = T[tid]["corruptions"]["superseded"]; x = abs(c["d_length"]) * math.exp(rng.uniform(-0.08, 0.08))
        ax.scatter([x], [100 * sum(v) / len(v) + rng.uniform(-1.6, 1.6)], s=13, color=LONGER if c["direction"] == "old_longer" else SHORTER, alpha=0.7, lw=0, zorder=3)
    for lo, hi in ((1, 5), (6, 50), (51, 10 ** 6)):
        tids = [tid for tid in per if lo <= abs(T[tid]["corruptions"]["superseded"]["d_length"]) <= hi]
        k = sum(sum(per[t]) for t in tids); n = sum(len(per[t]) for t in tids); p, el, eh = pct(k, n)
        xc = float(np.median([abs(T[t]["corruptions"]["superseded"]["d_length"]) for t in tids]))
        ax.errorbar(xc, p, yerr=[[el], [eh]], fmt="_", color=INK, ms=14, mew=1.6, capsize=2, lw=1.0, zorder=5)
        ax.text(xc, p - el - 4, f"{k}/{n}", ha="center", va="top", fontsize=6, color=INK)
    ax.set_xscale("log"); ax.set_ylim(50, 106); ax.set_xlabel("Size of the historical change in length (residues)")
    ax.set_ylabel("Runs relaying, per protein (%)"); ax.set_title("Every protein, three models × two record formats", loc="left")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=LONGER, label="superseded sequence longer"), Line2D([], [], marker="o", ls="", color=SHORTER, label="superseded sequence shorter"),
                       Line2D([], [], marker="_", ls="", color=INK, ms=10, mew=1.6, label="pooled rate per size bin")], loc="lower right", frameon=False)
    ax = fig.add_subplot(gs[1, 0:2]); letter(ax, "c"); groups = M3 + ["pooled"]
    for i, g in enumerate(groups):
        rs = [t for m in (M3 if g == "pooled" else [g]) for t in load(f"results/robustness/{m}_p5_annotate.jsonl", "superseded") if cov(t)]
        for j, (dirn, col, mk) in enumerate((("old_longer", LONGER, "^"), ("old_shorter", SHORTER, "v"))):
            sub = [t for t in rs if T[t["task_id"]]["direction"] == dirn]; p, el, eh = pct(*kn(sub)); xj = i + (-0.14 if j == 0 else 0.14)
            ax.errorbar(xj, p, yerr=[[el], [eh]], fmt=mk, color=col, ms=5, capsize=1.6, lw=0.8, zorder=4)
            ax.text(xj, p + eh + 2, f"{kn(sub)[0]}/{len(sub)}", ha="center", fontsize=5.8, color=MUTED)
    ax.set_xticks(range(len(groups))); ax.set_xticklabels([SHORT.get(g, "all three") for g in groups]); ax.set_ylim(0, 72)
    ax.set_ylabel("Relayed despite second source (%)"); ax.set_title("With AlphaFold DB as second source: residual relay by direction of the revision", loc="left")
    ax.grid(axis="x", visible=False)
    ax.legend(handles=[Line2D([], [], marker="^", ls="", color=LONGER, label="superseded longer than today"), Line2D([], [], marker="v", ls="", color=SHORTER, label="superseded shorter")], loc="upper right", frameon=False)
    ax = fig.add_subplot(gs[1, 2]); letter(ax, "d")
    for i, m in enumerate(M3):
        a = pct(*kn(load(f"results/phase5/{m}_summary.jsonl", "superseded")))
        b = pct(*kn([t for t in load(f"results/robustness/{m}_p5_annotate.jsonl", "superseded") if cov(t)]))
        ax.annotate("", xy=(i, b[0]), xytext=(i, a[0]), arrowprops=dict(arrowstyle="-|>", color=COL[m], lw=1.2))
        ax.errorbar(i, a[0], yerr=[[a[1]], [a[2]]], fmt="o", color=COL[m], mfc="white", ms=4.2, capsize=1.6, lw=0.8)
        ax.errorbar(i, b[0], yerr=[[b[1]], [b[2]]], fmt="o", color=COL[m], ms=4.2, capsize=1.6, lw=0.8)
        ax.text(i + 0.12, b[0], f"{b[0]:.0f}%", va="center", fontsize=6.2, color=COL[m])
    ax.set_xticks(range(3)); ax.set_xticklabels([SHORT[m] for m in M3]); ax.set_xlim(-0.5, 2.7); ax.set_ylim(-3, 106)
    ax.set_title("Without, then with, second source", loc="left"); ax.grid(axis="x", visible=False)
    fig.savefig(f"{OUT}/nmi_real_errors.pdf"); plt.close(fig)

# ------------------------------------------------------------------ Fig. 6
def reason(t):
    x = ((t.get("trace") or {}).get("final_text") or "").lower()
    if "canonical" in x: return "recalled canonical value"
    if "original" in x or "observed" in x: return "value from the verification note"
    return "other"

def fig6():
    from harness import second_source as ss
    T = {t["task_id"]: t for t in json.load(open("data/phase5_tasks.json"))["tasks"]}
    cov = lambda t: bool(ss._AF.get(T[t["task_id"]]["target_accession"]))
    M3 = ["opus5", "argon", "deepseek"]
    ARMS = [("p5_annotate", "annotate:\nconflict listed"), ("p5_replace", "replace:\nambiguous labels"),
            ("p5_replace_labeled", "replace:\noriginal labelled"), ("p5_replace_silent", "replace:\nsilent")]
    R = {(m, a): [t for t in load(f"results/robustness/{m}_{a}.jsonl", "superseded") if cov(t)] for m in M3 for a, _ in ARMS}
    fig = plt.figure(figsize=(TW, 5.0), layout="constrained"); gs = fig.add_gridspec(2, 1, height_ratios=[1.15, 1])
    ax = fig.add_subplot(gs[0]); letter(ax, "a")
    for gi, (a, _) in enumerate(ARMS):
        for mi, m in enumerate(M3):
            x = gi + (mi - 1) * 0.22; p, el, eh = pct(*kn(R[(m, a)]))
            ax.errorbar(x, p, yerr=[[el], [eh]], fmt="o", color=COL[m], ms=4.5, capsize=1.6, lw=0.8, zorder=4)
            samples(ax, x, R[(m, a)], COL[m])
            ax.text(x, p + eh + 1.5, f"{kn(R[(m, a)])[0]}/{len(R[(m, a)])}", ha="center", fontsize=5.6, color=MUTED, rotation=90, va="bottom")
    ax.set_xticks(range(len(ARMS))); ax.set_xticklabels([l for _, l in ARMS]); ax.set_ylim(-3, 62); ax.set_xlim(-0.5, len(ARMS) - 0.5)
    ax.set_ylabel("Superseded value relayed (%)"); ax.grid(axis="x", visible=False)
    ax.set_title("Real UniProt errors, covered proteins, three samples per run", loc="left")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=COL[m], label=NAME[m]) for m in M3] + [Line2D([], [], marker="o", ls="", color=INK, alpha=0.35, ms=2.5, label="single sample")],
              loc="upper right", frameon=False)
    ax = fig.add_subplot(gs[1]); letter(ax, "b")
    CATS = [("recalled canonical value", "#d4a017"), ("value from the verification note", "#c0392b"), ("other", "#c8c8c8")]
    rows = [(m, a, l) for a, l in ARMS[:3] for m in M3]
    for i, (m, a, l) in enumerate(rows):
        y = len(rows) - 1 - i; rel = [t for t in R[(m, a)] if t.get("propagated")]; cnt = collections.Counter(reason(t) for t in rel); left = 0
        for cat, col in CATS:
            ax.barh(y, cnt[cat], left=left, color=col, height=0.66, edgecolor="white", lw=0.4); left += cnt[cat]
        ax.text(left + 0.8, y, f"{len(rel)}", va="center", fontsize=6.2)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{SHORT[m]}, {l.split(':')[0]} ({l.split(chr(10))[1]})" for m, a, l in reversed(rows)])
    ax.set_xlabel("Relayed runs (count)"); ax.set_title("What the relayed answers cited (text match on the final answer)", loc="left"); ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=c, label=k) for k, c in CATS], loc="upper right", frameon=False)
    fig.savefig(f"{OUT}/nmi_presentation.pdf"); plt.close(fig)

for f in (fig1, fig3, fig4, fig5, fig6):
    f(); print("wrote", f.__name__)
