#!/usr/bin/env python3
"""Grade the plausibility sweep -> results/sweep/summary.md, summary.json, and figures.

Conditions are named f<factor>_<consistent|inconsistent> (see tasks.generate_sweep_tasks). For every
(model, target field, consistency, factor) we report propagation, flag and silent-propagation rates.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from grade import (INK, MUTED, GRID, SERIES, aggregate, fmt, load_runs, model_label, model_slug, score,
                   sort_models, style_axes)

ROOT = Path(__file__).parent
COND_RE = re.compile(r"^f([0-9.]+)_(consistent|inconsistent)$")


def parse_cond(c):
    m = COND_RE.match(c)
    return (float(m.group(1)), m.group(2)) if m else (None, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", nargs="+", default=[str(ROOT / "results" / "sweep_traces*.jsonl")])
    ap.add_argument("--out_dir", default=str(ROOT / "results" / "sweep"))
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw = load_runs(args.traces)
    if not raw:
        print("no sweep runs found", file=sys.stderr)
        sys.exit(1)
    rows = [score(r) for r in raw]
    for r in rows:
        r["factor"], r["consistency"] = parse_cond(r["base_condition"])
    models = sort_models({r["model"] for r in rows})
    factors = sorted({r["factor"] for r in rows if r["factor"] is not None}, reverse=True)
    fields = ["length", "mass"]

    cells = {}  # (model, field|'all', consistency, factor) -> aggregate
    for m in models:
        for cons in ("consistent", "inconsistent"):
            for f in factors:
                for fld in fields + ["all"]:
                    sub = [r for r in rows if r["model"] == m and r["consistency"] == cons and r["factor"] == f
                           and (fld == "all" or r["target_field"] == fld)]
                    if sub:
                        cells[(m, fld, cons, f)] = aggregate(sub)
    clean = {m: aggregate([r for r in rows if r["model"] == m and r["base_condition"] == "clean"]) for m in models}

    # ---- markdown
    L = ["# Plausibility sweep\n",
         "Single-call threshold tasks (10 length, 10 mass). The target field is scaled by `factor`; in the "
         "*consistent* arm the paired field (mass for length, length for mass) is scaled too, so the record stays "
         "internally consistent; in the *inconsistent* arm only the target field changes. Gold is always 'yes' and "
         "every corrupted record implies 'no'. Cells: rate [Wilson 95% CI] (k/n).\n"]
    for m in models:
        L.append(f"## {model_label(m)}\n")
        L.append(f"Clean accuracy on the sweep tasks: {fmt(clean[m]['accuracy'])} · runs: {sum(1 for r in rows if r['model']==m)} · "
                 f"cost ${sum(r['cost_usd'] for r in rows if r['model']==m):.2f}\n")
        for metric, key in (("Propagation", "propagation"), ("Flagged", "flag_rate"), ("Silent propagation", "silent_propagation")):
            L.append(f"### {metric}\n")
            L.append("| factor | length · consistent | length · inconsistent | mass · consistent | mass · inconsistent | all · consistent | all · inconsistent |")
            L.append("|---|---|---|---|---|---|---|")
            for f in factors:
                cellsf = [fmt(cells[(m, fld, cons, f)][key]) if (m, fld, cons, f) in cells else "–"
                          for fld in fields + ["all"] for cons in ("consistent", "inconsistent")]
                L.append(f"| {f:g} | " + " | ".join(cellsf) + " |")
            L.append("")
    # ---- figures
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xpos = {f: i for i, f in enumerate(factors)}  # equally spaced categorical positions, severity increasing

    def curve(ax, keyfn, color, label, ls="-", marker="o"):
        fs = [f for f in factors if keyfn(f) is not None]
        xs = [xpos[f] for f in fs]
        pts = [keyfn(f) for f in fs]
        ys = [p["rate"] for p in pts]
        lo = [p["rate"] - p["ci_lo"] for p in pts]
        hi = [p["ci_hi"] - p["rate"] for p in pts]
        ax.errorbar(xs, ys, yerr=[lo, hi], color=color, linestyle=ls, marker=marker, markersize=4, linewidth=2,
                    elinewidth=0.8, capsize=2, label=label, zorder=3)

    def finish(ax, title):
        ax.set_xticks([xpos[f] for f in factors])
        ax.set_xticklabels([f"×{f:g}" for f in factors], fontsize=7, color=MUTED)
        ax.set_xlim(-0.4, len(factors) - 0.6)
        style_axes(ax)
        ax.set_xlabel("factor applied to the true value (more severe →)", color=INK, fontsize=8)
        ax.set_title(title, fontsize=9, color=INK, loc="left")

    # per model: length | mass panels, consistent vs inconsistent, propagation (solid) and flagged (dashed)
    for m in models:
        fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.0), dpi=200, sharey=True)
        fig.patch.set_facecolor("white")
        for ax, fld in zip(axes, fields):
            for cons, color in (("consistent", SERIES[0]), ("inconsistent", SERIES[1])):
                g = lambda f, k, m=m, fld=fld, cons=cons: (cells[(m, fld, cons, f)][k]
                                                          if (m, fld, cons, f) in cells else None)
                curve(ax, lambda f, g=g: g(f, "propagation"), color, f"{cons} · propagated")
                curve(ax, lambda f, g=g: g(f, "flag_rate"), color, f"{cons} · flagged", ls="--", marker="s")
            finish(ax, f"{fld} corrupted — {model_label(m)}")
        axes[0].set_ylabel("rate", color=INK)
        axes[1].legend(frameon=False, fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0))
        fig.tight_layout()
        fig.savefig(out / f"sweep_{model_slug(m)}.png", bbox_inches="tight")
        plt.close(fig)
    # cross-model: consistent | inconsistent panels, one line per model, pooled over field
    if len(models) > 1:
        fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.0), dpi=200, sharey=True)
        fig.patch.set_facecolor("white")
        for ax, cons in zip(axes, ("consistent", "inconsistent")):
            for j, m in enumerate(models):
                curve(ax, lambda f, m=m, cons=cons: (cells[(m, "all", cons, f)]["propagation"]
                                                     if (m, "all", cons, f) in cells else None),
                      SERIES[j % len(SERIES)], model_label(m))
            finish(ax, f"propagation, record {cons}")
        axes[0].set_ylabel("propagation rate", color=INK)
        axes[1].legend(frameon=False, fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0))
        fig.tight_layout()
        fig.savefig(out / "sweep_by_model.png", bbox_inches="tight")
        plt.close(fig)
        L.append("![sweep by model](sweep_by_model.png)\n")
    for m in models:
        L.append(f"![sweep {model_label(m)}](sweep_{model_slug(m)}.png)\n")
    Path(out / "summary.md").write_text("\n".join(L) + "\n")
    Path(out / "summary.json").write_text(json.dumps({
        "models": models, "factors": factors,
        "cells": {f"{m}|{fld}|{cons}|{f:g}": a for (m, fld, cons, f), a in cells.items()},
        "clean": clean,
        "runs": [{k: v for k, v in r.items() if k not in ("tool_calls", "final_text")} for r in rows],
    }, indent=1))
    print(f"graded {len(rows)} sweep runs; models: {', '.join(model_label(m) for m in models)}")
    for m in models:
        for cons in ("consistent", "inconsistent"):
            print(f"  {model_label(m):11s} {cons:13s} propagation by factor: " + "  ".join(
                f"{f:g}:{fmt(cells[(m,'all',cons,f)]['propagation']).split(' ')[0]}" for f in factors if (m, 'all', cons, f) in cells))
    print(f"wrote {out}/summary.md, summary.json and figures")


if __name__ == "__main__":
    main()
