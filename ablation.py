#!/usr/bin/env python3
"""Reasoning ablation: Sonnet 5 with thinking disabled vs adaptive, main experiment.
Reads results/traces.jsonl (adaptive) and results/ablation_nothink_sonnet5.jsonl (disabled);
writes paper/tables/ablation.tex and paper/ablation.json."""
import json
from pathlib import Path

from analysis import classify, wilson
from grade import load_runs, score

ROOT = Path(__file__).parent
OUT = ROOT / "paper"
CONDS = ["clean", "impossible", "plausible", "clean+verify", "impossible+verify", "plausible+verify"]


def summarise(rows):
    n = len(rows)
    k = sum(bool(r["propagated"]) for r in rows); npr = sum(r["propagated"] is not None for r in rows)
    out = {"n": n, "accuracy": sum(r["correct"] for r in rows) / n, "flagged": sum(r["flagged"] for r in rows) / n,
           "silent": sum(r["silent_propagation"] for r in rows) / n, "recall": sum(r["recalled_tool"] for r in rows) / n,
           "tool_calls": sum(r["n_tool_calls"] for r in rows) / n, "any_tool": sum(r["n_tool_calls"] > 0 for r in rows) / n,
           "saw_corrupt": sum(any(c.get("corrupted") for c in r["tool_calls"]) for r in rows) / n,
           "parse_fail": sum(not r["parsed_ok"] for r in rows), "cost": sum(r["cost_usd"] for r in rows)}
    if npr:
        out["propagation"] = k / npr; out["prop_ci"] = wilson(k, npr); out["prop_kn"] = f"{k}/{npr}"
    else:
        out["propagation"] = None
    return out


def main():
    adaptive = [score(r) for r in load_runs([str(ROOT / "results" / "traces.jsonl")]) if r["model"] == "claude-sonnet-5" and r["thinking"] == "adaptive"]
    disabled = [score(r) for r in load_runs([str(ROOT / "results" / "ablation_nothink_sonnet5.jsonl")])]
    res = {}
    for name, rows in (("adaptive", adaptive), ("disabled", disabled)):
        for c in CONDS:
            sub = [r for r in rows if r["condition"] == c]
            if sub:
                res[f"{name}|{c}"] = summarise(sub)
    # cue composition of flagged corrupted runs, baseline prompt
    cues = {}
    for name, rows in (("adaptive", adaptive), ("disabled", disabled)):
        for c in ("impossible", "plausible"):
            fl = [r for r in rows if r["condition"] == c and r["flagged"]]
            labs = [classify(r["concerns"]) for r in fl]
            cues[f"{name}|{c}"] = {"n": len(fl), **{k: (sum(l[k] for l in labs) / len(labs) if labs else None) for k in ("crossfield", "recall", "rule")}}
    (OUT / "ablation.json").write_text(json.dumps({"summary": res, "cues": cues}, indent=1))

    P = lambda v: "--" if v is None else f"{100 * v:.0f}"
    L = ["\\begin{tabular}{llrrrrrrrr}", "\\toprule",
         "condition & thinking & $n$ & accuracy & propagation & 95\\% CI & flagged & silent & tool calls & saw corrupted \\\\", "\\midrule"]
    for c in CONDS:
        for name in ("adaptive", "disabled"):
            s = res.get(f"{name}|{c}")
            if not s:
                continue
            prop = P(s["propagation"]); ci = f"[{100*s['prop_ci'][0]:.0f}, {100*s['prop_ci'][1]:.0f}]" if s["propagation"] is not None else "--"
            L.append(f"{c.replace('+verify', ' + verify')} & {name} & {s['n']} & {P(s['accuracy'])} & {prop} & {ci} & {P(s['flagged'])} & {P(s['silent'])} & {s['tool_calls']:.2f} & {P(s['saw_corrupt']) if not c.startswith('clean') else '--'} \\\\")
        if c in ("plausible",):
            L.append("\\addlinespace[2pt]")
    L += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "ablation.tex").write_text("\n".join(L) + "\n")
    for k, s in res.items():
        print(f"{k:28s} n={s['n']:3d} acc={P(s['accuracy'])}% prop={P(s['propagation'])}% {s.get('prop_kn','')} flag={P(s['flagged'])}% silent={P(s['silent'])}% recall={P(s['recall'])}% calls={s['tool_calls']:.2f} any_tool={P(s['any_tool'])}% saw_corrupt={P(s['saw_corrupt'])}% parse_fail={s['parse_fail']} cost=${s['cost']:.2f}")
    for k, v in cues.items():
        print(f"cues {k:22s} n={v['n']:3d} crossfield={P(v['crossfield'])}% recall={P(v['recall'])}% rule={P(v['rule'])}%")


if __name__ == "__main__":
    main()


def compact_table():
    res = json.loads((OUT / "ablation.json").read_text())["summary"]
    P = lambda v: f"{100 * v:.0f}"
    L = ["\\begin{tabular}{lrrrrrr}", "\\toprule",
         " & \\multicolumn{2}{c}{propagation [95\\% CI]} & \\multicolumn{2}{c}{flagged} & \\multicolumn{2}{c}{silent} \\\\",
         "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}",
         "condition & adaptive & disabled & adaptive & disabled & adaptive & disabled \\\\", "\\midrule"]
    for c in ("impossible", "plausible", "impossible+verify", "plausible+verify"):
        a, d = res[f"adaptive|{c}"], res[f"disabled|{c}"]
        f = lambda s: f"{P(s['propagation'])} [{100*s['prop_ci'][0]:.0f}, {100*s['prop_ci'][1]:.0f}]"
        L.append(f"{c.replace('+verify', ' + verify')} & {f(a)} & {f(d)} & {P(a['flagged'])} & {P(d['flagged'])} & {P(a['silent'])} & {P(d['silent'])} \\\\")
    L += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "tables" / "ablation_compact.tex").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    compact_table()
