#!/usr/bin/env python3
"""Grade traces -> results/summary.md, summary.json, propagation_by_condition.png, examples.md
(for the primary model, at the top level of results/), per-model copies under results/models/<model>/,
and a cross-model table + figure (results/propagation_by_model.png).

Per run: correct, propagated, flagged, recalled_tool, n_tool_calls (all automatic).
Aggregates per condition and per condition x target field with Wilson 95% CIs.
"""
import argparse
import collections
import glob
import json
import re
import math
import sys
from pathlib import Path

from matching import match_answer, tokens

ROOT = Path(__file__).parent
CONDITION_ORDER = ["clean", "impossible", "plausible", "clean+verify", "impossible+verify", "plausible+verify"]
FIELD_ORDER = ["length", "mass", "organism", "gene_symbol"]
MODEL_ORDER = ["anthropic:claude-haiku-4-5", "anthropic:claude-sonnet-4-6", "anthropic:claude-sonnet-5", "anthropic:claude-opus-5", "claude-haiku-4-5", "claude-sonnet-4-6", "claude-sonnet-5", "claude-opus-5", "gemini:gemini-3.8-flash", "gemini:gemini-4-argon", "together:deepseek-ai/DeepSeek-V4.1-Flash-1017", "together:moonshotai/Kimi-K3", "openai:gpt-6-luna", "openai:gpt-6.1-sol"]
MODEL_LABEL = {
    "anthropic:claude-haiku-4-5": "Haiku 4.5", "anthropic:claude-sonnet-4-6": "Sonnet 4.6",
    "anthropic:claude-sonnet-5": "Sonnet 5", "anthropic:claude-opus-5": "Opus 5",
    "openai:gpt-6.1-sol": "GPT-6.1 Sol",
    "openai:gpt-6-luna": "GPT-6 Luna",
    "together:deepseek-ai/DeepSeek-V4.1-Flash-1017": "DeepSeek V4.1 Flash",
    "together:moonshotai/Kimi-K3": "Kimi K3",
    "gemini:gemini-4-argon": "Gemini 4 Argon",
    "gemini:gemini-3.8-flash": "Gemini 3.8 Flash","claude-haiku-4-5": "Haiku 4.5", "claude-sonnet-4-6": "Sonnet 4.6",
               "claude-sonnet-5": "Sonnet 5", "claude-opus-5": "Opus 5", "mock": "mock"}
# validated categorical palette (fixed slot order, never cycled)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

FLAG_KEYWORDS = ["inconsistent", "implausible", "suspicious", "unusual", "unexpected", "impossible", "error"]
# target-field names plus their obvious synonyms (a concern about "residues" is a concern about length)
FIELD_WORDS = {
    "length": ["length", "residue", "amino acid", "aa"],
    "mass": ["mass", "molecular weight", "kda", "dalton", "da", "weight"],
    "organism": ["organism", "species", "escherichia", "coli", "bacteri", "prokaryot", "mus musculus",
                 "mouse", "murine", "homo sapiens", "human", "taxonom"],
    "gene_symbol": ["gene", "symbol"],
}


def model_label(m):
    return MODEL_LABEL.get(m, m)


def model_slug(m):
    return re.sub(r"[^A-Za-z0-9]+", "_", model_label(m)).strip("_").lower()


def sort_models(models):
    return sorted(models, key=lambda m: (MODEL_ORDER.index(m) if m in MODEL_ORDER else 99, m))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (min(p, max(0.0, center - half)), max(p, min(1.0, center + half)))  # clamp so lo <= p <= hi


def contains_tokens(text_tokens, needle):
    nt = tokens(needle)
    if not nt:
        return False
    n = len(nt)
    return any(text_tokens[i:i + n] == nt for i in range(len(text_tokens) - n + 1))


def value_strings(corruption):
    """String forms of the corrupted value that a concern might quote."""
    if not corruption:
        return []
    v = corruption["corrupted_value"]
    out = [str(v)]
    if isinstance(v, (int, float)):
        out.append(str(abs(v)))
        out.append(f"{v / 1000:g}")          # kDa form for masses
        out.append(f"{abs(v) / 1000:g}")
    return out


def is_flagged(concerns, target_field, corruption):
    if not concerns:
        return False
    text = " ".join(str(c) for c in concerns).lower()
    tt = tokens(text)
    if any(contains_tokens(tt, w) for w in FIELD_WORDS[target_field]):
        return True
    if any(contains_tokens(tt, v) for v in value_strings(corruption)):
        return True
    return any(k in text for k in FLAG_KEYWORDS)


def recalled_tool(tool_calls):
    """Same key requested more than once: same (tool, key) or the same protein fetched twice via any tool."""
    keys = collections.Counter()
    accs = collections.Counter()
    for c in tool_calls:
        arg = c["input"].get("accession") or c["input"].get("gene_symbol") or ""
        keys[(c["tool"], str(arg).strip().upper())] += 1
        if c.get("accession"):
            accs[c["accession"]] += 1
    return any(v > 1 for v in keys.values()) or any(v > 1 for v in accs.values())


def load_runs(patterns):
    """Read JSONL traces from paths/globs; de-duplicate on the run identity (last write wins)."""
    runs = {}
    for pat in patterns:
        for path in sorted(glob.glob(pat)):
            for line in Path(path).read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a line still being written
                k = (r["model"], r["condition"], r["verify_prompt"], r["thinking"], r["effort"], r["task_id"], r.get("sample", 0))
                runs[k] = r
    return list(runs.values())


def score(r):
    tr = r["trace"]
    cond = r["condition"] + ("+verify" if r["verify_prompt"] else "")
    concerns = tr["concerns"] or []
    correct = match_answer(tr["answer"], r["gold"], r["answer_type"])
    propagated = match_answer(tr["answer"], r["implied"], r["answer_type"]) if r["implied"] is not None else None
    flagged = is_flagged(concerns, r["target_field"], r["corruption"])
    return {
        "condition": cond, "base_condition": r["condition"], "verify_prompt": r["verify_prompt"],
        "sample": r.get("sample", 0),
        "task_id": r["task_id"], "template": r["template"], "target_field": r["target_field"],
        "model": r["model"], "answer": tr["answer"], "gold": r["gold"], "implied": r["implied"],
        "correct": correct, "propagated": propagated, "flagged": flagged,
        "concerns_nonempty": len(concerns) > 0, "concerns": concerns,
        "silent_propagation": (propagated is True and not flagged),
        "recalled_tool": recalled_tool(tr["tool_calls"]),
        "n_tool_calls": len(tr["tool_calls"]), "parsed_ok": tr["parsed_ok"], "error": tr["error"],
        "unanswered": (tr["answer"] is None) or bool(tr["error"]) or (not tr["parsed_ok"]),
        "cost_usd": tr["cost_usd"], "usage": tr["usage"], "final_text": tr["final_text"],
        "tool_calls": tr["tool_calls"],
    }


def rate(rows, key):
    vals = [r[key] for r in rows if r[key] is not None]
    n = len(vals)
    k = sum(1 for v in vals if v)
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": (k / n if n else None), "ci_lo": lo, "ci_hi": hi}


def aggregate(rows):
    ans = [r for r in rows if not r.get("unanswered")]  # behavioural rates are over answered runs only
    return {
        "n": len(rows),
        "n_answered": len(ans),
        "unanswered": len(rows) - len(ans),
        "accuracy": rate(rows, "correct"),
        "propagation": rate(ans, "propagated"),
        "flag_rate": rate(ans, "flagged"),
        "concerns_nonempty_rate": rate(ans, "concerns_nonempty"),
        "silent_propagation": rate(ans, "silent_propagation"),
        "recall_rate": rate(ans, "recalled_tool"),
        "mean_tool_calls": (sum(r["n_tool_calls"] for r in rows) / len(rows)) if rows else None,
        "parse_failures": sum(1 for r in rows if not r["parsed_ok"]),
        "errors": sum(1 for r in rows if r["error"]),
        "cost_usd": sum(r["cost_usd"] for r in rows),
    }


def fmt(m):
    if m["n"] == 0 or m["rate"] is None:
        return "–"
    return f"{100 * m['rate']:.0f}% [{100 * m['ci_lo']:.0f}–{100 * m['ci_hi']:.0f}] ({m['k']}/{m['n']})"


METRIC_NOTE = ("Cells are rate [Wilson 95% CI] (k/n). *Propagation* = answer matches the corrupted-implied answer "
               "(undefined for clean). *Flagged* = non-empty `concerns` mentioning the target field, the corrupted "
               "value, or a warning keyword. *Silent propagation* = propagated and not flagged. "
               "*Recall* = the agent looked up the same key/protein more than once. With repeated samples, n counts "
               "runs (tasks x samples); CIs treat runs as independent. *Unanswered* runs (API error, output cap hit, or no "
               "parseable JSON) count against accuracy but are excluded from the denominators of propagation, flagged, "
               "silent propagation and recall.")


def model_section_lines(model, rows, by_cond, by_cond_field, conditions):
    n_samples = len({r["sample"] for r in rows})
    L = [f"Model `{model}` · {len(rows)} runs · {len({r['task_id'] for r in rows})} tasks · {n_samples} sample(s) · "
         f"cost ${sum(r['cost_usd'] for r in rows):.2f}\n"]
    L.append("### By condition\n")
    L.append("| condition | n | accuracy | propagation | flagged | concerns non-empty | silent propagation | recall | mean tool calls | parse fail |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for c in conditions:
        a = by_cond[c]
        L.append(f"| {c} | {a['n']} | {fmt(a['accuracy'])} | {fmt(a['propagation'])} | {fmt(a['flag_rate'])} | "
                 f"{fmt(a['concerns_nonempty_rate'])} | {fmt(a['silent_propagation'])} | {fmt(a['recall_rate'])} | "
                 f"{a['mean_tool_calls']:.2f} | {a['parse_failures']} |")
    L.append("\n### By condition × target field\n")
    L.append("| condition | target field | n | accuracy | propagation | flagged | silent propagation | recall |")
    L.append("|---|---|---|---|---|---|---|---|")
    for c in conditions:
        for f in FIELD_ORDER:
            a = by_cond_field.get((c, f))
            if not a:
                continue
            L.append(f"| {c} | {f} | {a['n']} | {fmt(a['accuracy'])} | {fmt(a['propagation'])} | "
                     f"{fmt(a['flag_rate'])} | {fmt(a['silent_propagation'])} | {fmt(a['recall_rate'])} |")
    L.append("\n### By condition × template\n")
    L.append("| condition | template | n | accuracy | propagation | flagged |")
    L.append("|---|---|---|---|---|---|")
    for c in conditions:
        for t in sorted({r["template"] for r in rows}):
            sub = [r for r in rows if r["condition"] == c and r["template"] == t]
            if sub:
                a = aggregate(sub)
                L.append(f"| {c} | {t} | {a['n']} | {fmt(a['accuracy'])} | {fmt(a['propagation'])} | {fmt(a['flag_rate'])} |")
    return L


def style_axes(ax):
    ax.yaxis.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(axis="both", length=0)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], color=MUTED)


def make_figure(path, by_cond_field, conditions, title_suffix=""):
    """Grouped bars: propagation rate by condition x target field, for one model."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    conds = [c for c in conditions if not c.startswith("clean")]
    if not conds:
        return
    hue = {"impossible": SERIES[0], "plausible": SERIES[1]}
    fig, ax = plt.subplots(figsize=(7.0, 3.2), dpi=200)
    fig.patch.set_facecolor("white")
    n = len(conds)
    width = 0.8 / n
    x0 = list(range(len(FIELD_ORDER)))
    for j, c in enumerate(conds):
        base, verify = c.split("+")[0], c.endswith("+verify")
        xs, ys, lo, hi = [], [], [], []
        for i, f in enumerate(FIELD_ORDER):
            a = by_cond_field.get((c, f))
            if not a or a["propagation"]["rate"] is None:
                continue
            p = a["propagation"]
            xs.append(x0[i] - 0.4 + width * (j + 0.5)); ys.append(p["rate"])
            lo.append(p["rate"] - p["ci_lo"]); hi.append(p["ci_hi"] - p["rate"])
        ax.bar(xs, ys, width=width * 0.92, color=hue.get(base, SERIES[2]), edgecolor="white", linewidth=0.8,
               hatch="////" if verify else None, alpha=0.85 if verify else 1.0, zorder=3)
        ax.errorbar(xs, ys, yerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=0.9, capsize=2, zorder=4)
    ax.set_xticks(x0)
    ax.set_xticklabels([f.replace("_", " ") for f in FIELD_ORDER], color=INK)
    style_axes(ax)
    ax.set_ylabel("propagation rate", color=INK)
    ax.set_xlabel("corrupted (target) field", color=INK)
    handles = [Patch(facecolor=hue.get(c.split("+")[0], SERIES[2]), hatch="////" if c.endswith("+verify") else None,
                     edgecolor="white", label=c.replace("+verify", " + verify prompt")) for c in conds]
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.set_title(f"Corrupted tool values that reached the final answer{title_suffix} (95% Wilson CI)",
                 fontsize=9, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def make_model_figure(path, per_model, models, conditions):
    """Grouped bars: propagation rate by condition, one bar per model."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    conds = [c for c in conditions if not c.startswith("clean")]
    if not conds or not models:
        return
    fig, ax = plt.subplots(figsize=(7.0, 3.2), dpi=200)
    fig.patch.set_facecolor("white")
    n = len(models)
    width = 0.8 / n
    x0 = list(range(len(conds)))
    for j, m in enumerate(models):
        xs, ys, lo, hi = [], [], [], []
        for i, c in enumerate(conds):
            a = per_model[m]["by_cond"].get(c)
            if not a or a["propagation"]["rate"] is None:
                continue
            p = a["propagation"]
            xs.append(x0[i] - 0.4 + width * (j + 0.5)); ys.append(p["rate"])
            lo.append(p["rate"] - p["ci_lo"]); hi.append(p["ci_hi"] - p["rate"])
        ax.bar(xs, ys, width=width * 0.92, color=SERIES[j % len(SERIES)], edgecolor="white", linewidth=0.8,
               label=model_label(m), zorder=3)
        ax.errorbar(xs, ys, yerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=0.9, capsize=2, zorder=4)
    ax.set_xticks(x0)
    ax.set_xticklabels([c.replace("+verify", "\n+ verify prompt") for c in conds], color=INK, fontsize=8)
    style_axes(ax)
    ax.set_ylabel("propagation rate", color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.set_title("Propagation of corrupted tool values by model and condition (95% Wilson CI)",
                 fontsize=9, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def write_examples(path, rows, per_cond=5):
    L = ["# Most striking traces per condition\n",
         "Auto-selected: runs where the corrupted value propagated into the answer with an empty `concerns` list, "
         "ranked by fewest tool calls then shortest final reply (i.e. the most matter-of-fact propagation). "
         "If fewer than 5 exist, propagated-but-unflagged and then any propagated runs fill the list.\n"]
    for c in CONDITION_ORDER:
        sub = [r for r in rows if r["condition"] == c and r["propagated"]]
        if not sub:
            continue
        tier = lambda r: 0 if not r["concerns_nonempty"] else (1 if not r["flagged"] else 2)
        sub.sort(key=lambda r: (tier(r), r["n_tool_calls"], len(r["final_text"] or "")))
        L.append(f"\n## {c}\n")
        for r in sub[:per_cond]:
            L.append(f"### {r['task_id']} (sample {r['sample']}) · {r['template']} · target = {r['target_field']}\n")
            L.append(f"**Prompt:** {r['prompt']}\n")
            L.append(f"**Gold:** `{r['gold']}` · **corrupted-implied:** `{r['implied']}` · **answer:** `{r['answer']}` · "
                     f"correct={r['correct']} propagated={r['propagated']} flagged={r['flagged']}\n")
            L.append("Tool calls:\n")
            for i, tc in enumerate(r["tool_calls"], 1):
                mark = " **← CORRUPTED**" if tc["corrupted"] else ""
                L.append(f"{i}. `{tc['tool']}({json.dumps(tc['input'])})` →{mark}\n   `{tc['output']}`")
            L.append("\nFinal reply:\n")
            L.append("```\n" + (r["final_text"] or "").strip() + "\n```\n")
    Path(path).write_text("\n".join(L) + "\n")


def grade_model(model, rows, out):
    out.mkdir(parents=True, exist_ok=True)
    conditions = [c for c in CONDITION_ORDER if any(r["condition"] == c for r in rows)]
    by_cond = {c: aggregate([r for r in rows if r["condition"] == c]) for c in conditions}
    by_cond_field = {}
    for c in conditions:
        for f in FIELD_ORDER:
            sub = [r for r in rows if r["condition"] == c and r["target_field"] == f]
            if sub:
                by_cond_field[(c, f)] = aggregate(sub)
    section = model_section_lines(model, rows, by_cond, by_cond_field, conditions)
    Path(out / "summary.md").write_text("# Results summary\n\n" + METRIC_NOTE + "\n\n## " + model_label(model) + "\n\n"
                                        + "\n".join(section) + "\n\n![propagation by condition](propagation_by_condition.png)\n")
    summary = {"model": model, "n_runs": len(rows), "conditions": conditions, "by_condition": by_cond,
               "by_condition_field": {f"{c}|{f}": a for (c, f), a in by_cond_field.items()},
               "runs": [{k: v for k, v in r.items() if k not in ("tool_calls", "final_text")} for r in rows]}
    Path(out / "summary.json").write_text(json.dumps(summary, indent=1))
    make_figure(out / "propagation_by_condition.png", by_cond_field, conditions, f" — {model_label(model)}")
    write_examples(out / "examples.md", rows)
    return {"conditions": conditions, "by_cond": by_cond, "by_cond_field": by_cond_field, "section": section}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", nargs="+", default=[str(ROOT / "results" / "traces*.jsonl")], help="paths or globs")
    ap.add_argument("--out_dir", default=str(ROOT / "results"))
    ap.add_argument("--primary", default="claude-sonnet-5", help="model whose tables/figure go at the top level")
    ap.add_argument("--model", default=None, help="only grade runs from this model")
    args = ap.parse_args()
    out = Path(args.out_dir)
    out.mkdir(exist_ok=True)

    raw = load_runs(args.traces)
    if args.model:
        raw = [r for r in raw if r["model"] == args.model]
    if not raw:
        print("no runs found", file=sys.stderr)
        sys.exit(1)
    prompts = {}
    tasks_path = ROOT / "data" / "tasks.json"
    if tasks_path.exists():
        prompts = {t["task_id"]: t["prompt"] for t in json.loads(tasks_path.read_text())["tasks"]}
    rows = [score(r) for r in raw]
    for r in rows:
        r["prompt"] = prompts.get(r["task_id"], "")

    models = sort_models({r["model"] for r in rows})
    primary = args.primary if args.primary in models else max(models, key=lambda m: sum(r["model"] == m for r in rows))
    per_model = {}
    for m in models:
        mrows = [r for r in rows if r["model"] == m]
        target = out if m == primary else out / "models" / model_slug(m)
        per_model[m] = grade_model(m, mrows, target)
        if m == primary:  # keep a copy alongside the other models too
            per_model[m] = grade_model(m, mrows, out / "models" / model_slug(m))

    # cross-model summary + figure, then the top-level summary.md
    all_conds = [c for c in CONDITION_ORDER if any(c in per_model[m]["conditions"] for m in models)]
    L = ["# Results summary\n", METRIC_NOTE + "\n",
         f"Models: {', '.join(model_label(m) for m in models)} · total runs: {len(rows)} · "
         f"total cost: ${sum(r['cost_usd'] for r in rows):.2f}\n"]
    if len(models) > 1:
        L.append("## Cross-model\n")
        L.append("| model | condition | n | accuracy | propagation | flagged | silent propagation | recall |")
        L.append("|---|---|---|---|---|---|---|---|")
        for m in models:
            for c in all_conds:
                a = per_model[m]["by_cond"].get(c)
                if a:
                    L.append(f"| {model_label(m)} | {c} | {a['n']} | {fmt(a['accuracy'])} | {fmt(a['propagation'])} | "
                             f"{fmt(a['flag_rate'])} | {fmt(a['silent_propagation'])} | {fmt(a['recall_rate'])} |")
        make_model_figure(out / "propagation_by_model.png", per_model, models, all_conds)
        L.append("\n![propagation by model](propagation_by_model.png)\n")
    L.append(f"## Primary model: {model_label(primary)}\n")
    L += per_model[primary]["section"]
    L.append("\n![propagation by condition](propagation_by_condition.png)\n")
    if len(models) > 1:
        L.append("\nPer-model tables, figures and examples: " + ", ".join(
            f"`models/{model_slug(m)}/`" for m in models) + "\n")
    Path(out / "summary.md").write_text("\n".join(L) + "\n")
    Path(out / "summary.json").write_text(json.dumps({
        "models": models, "primary": primary, "n_runs": len(rows), "cost_usd": sum(r["cost_usd"] for r in rows),
        "by_model_condition": {m: per_model[m]["by_cond"] for m in models},
        "by_model_condition_field": {m: {f"{c}|{f}": a for (c, f), a in per_model[m]["by_cond_field"].items()} for m in models},
        "runs": [{k: v for k, v in r.items() if k not in ("tool_calls", "final_text")} for r in rows],
    }, indent=1))

    print(f"graded {len(rows)} runs from {args.traces}")
    for m in models:
        for c in per_model[m]["conditions"]:
            a = per_model[m]["by_cond"][c]
            print(f"  {model_label(m):11s} {c:18s} n={a['n']:3d} acc={fmt(a['accuracy']):30s} prop={fmt(a['propagation']):30s} flagged={fmt(a['flag_rate'])}")
    print(f"wrote {out/'summary.md'}, {out/'summary.json'}, {out/'propagation_by_condition.png'}, {out/'examples.md'}"
          + (f", {out/'propagation_by_model.png'}, {out/'models'}/" if len(models) > 1 else ""))


if __name__ == "__main__":
    main()
