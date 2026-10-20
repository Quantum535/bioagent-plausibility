#!/usr/bin/env python3
"""Run the agent over tasks x conditions, cache every run, append full traces to results/traces.jsonl.

  python run.py --conditions clean impossible plausible --n_tasks 3    # smoke test + cost estimate
  python run.py --conditions clean impossible plausible --n_tasks 40
  python run.py --conditions clean impossible plausible --n_tasks 40 --verify_prompt   # 4th condition
  python run.py --model openai:<model> --n_tasks 40                                    # other providers
"""
import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agent import prompt_hash, run_agent, run_mock_agent, system_prompt
from corrupt import apply_corruption
from matching import match_answer
from providers import make_provider
from tools import CorruptingToolLayer, ProteinTable, render_record, tool_schemas

ROOT = Path(__file__).parent
CACHE_DIR = ROOT / "cache"
HARD_CAP = 600
DEFAULT_MODEL = os.environ.get("MODEL", "claude-sonnet-5")


def cache_key(model, condition, task_id, phash, sample=0):
    base = f"{model}|{condition}|{task_id}|{phash}" + (f"|s{sample}" if sample else "")
    return hashlib.sha256(base.encode()).hexdigest()[:24]


def check_no_leak(trace, task, condition, table):
    """Assert clean runs saw only clean records and corrupted runs saw the corrupted target record."""
    by_acc = {r["accession"]: r for r in table.records}
    for c in trace["tool_calls"]:
        if c["is_error"]:
            continue
        clean = render_record(table, by_acc[c["accession"]])
        if condition == "clean":
            assert not c["corrupted"] and c["output"] == clean, f"LEAK: corrupted record in clean run {task['task_id']}"
        elif c["accession"] == task["target_accession"]:
            expect = render_record(table, by_acc[c["accession"]], task["corruptions"][condition])
            assert c["corrupted"] and c["output"] == expect, f"target record not corrupted in {task['task_id']}/{condition}"
        else:
            assert not c["corrupted"] and c["output"] == clean, f"non-target record altered in {task['task_id']}/{condition}"


def _round_text(content):
    """Visible text of one API round, for either the Anthropic (list of blocks) or OpenAI (dict) trace shape."""
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text").strip()
    if isinstance(content, dict):
        return (content.get("content") or "").strip()
    return ""


def print_trace(rec):
    print("=" * 100)
    print(f"[{rec['condition']}{'+verify' if rec['verify_prompt'] else ''}] {rec['task_id']} ({rec['template']}, target={rec['target_field']})")
    print("PROMPT:", rec["trace"]["task_prompt"])
    for i, c in enumerate(rec["trace"]["tool_calls"], 1):
        flag = "  <-- CORRUPTED" if c["corrupted"] else ""
        print(f"  tool {i}: {c['tool']}({json.dumps(c['input'])}) -> {c['output']}{flag}")
    for r in rec["trace"]["rounds"]:
        txt = _round_text(r["content"])
        if txt:
            print(f"  assistant (round {r['round']}): {txt[:600]}")
    print(f"  ANSWER={rec['trace']['answer']!r}  gold={rec['gold']!r}  implied={rec['implied']!r}  "
          f"correct={rec['correct']} propagated={rec['propagated']}  concerns={rec['trace']['concerns']}")
    print(f"  cost=${rec['trace']['cost_usd']:.4f}  tokens={rec['trace']['usage']}  stop={rec['trace']['stop_reason']}  error={rec['trace']['error']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", nargs="+", default=["clean", "impossible", "plausible"],
                    help="'clean' or any corruption name defined in the task file")
    ap.add_argument("--samples", type=int, default=1, help="independent repeats of every (task, condition)")
    ap.add_argument("--sample_start", type=int, default=0, help="first sample index (0 = the original run)")
    ap.add_argument("--n_tasks", type=int, default=40)
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help="'claude-sonnet-5' (Anthropic), or 'openai:<model>', 'together:<org/model>'")
    ap.add_argument("--seed", type=int, default=0, help="must match the seed used by make_tasks.py")
    ap.add_argument("--verify_prompt", action="store_true", help="append the sanity-check sentence to the system prompt")
    ap.add_argument("--thinking", choices=["adaptive", "disabled"], default="adaptive")
    ap.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tasks", default=str(ROOT / "data" / "tasks.json"))
    ap.add_argument("--record_format", choices=["summary", "full"], default="summary",
                    help="summary = 7-field mock record; full = real UniProtKB entry (minus references/xrefs)")
    ap.add_argument("--proteins", default=None, help="protein table; default is the one named in the task file, else data/proteins.json")
    ap.add_argument("--out", default=str(ROOT / "results" / "traces.jsonl"))
    ap.add_argument("--mock", action="store_true", help="scripted tool-trusting agent, no API calls (pipeline test)")
    ap.add_argument("--no_cache", action="store_true")
    ap.add_argument("--yes", action="store_true", help=f"allow more than {HARD_CAP} runs without asking")
    ap.add_argument("--quiet", action="store_true", help="do not print traces (they are printed when n_tasks <= 3)")
    args = ap.parse_args()

    tasks_file = json.loads(Path(args.tasks).read_text())
    if tasks_file["seed"] != args.seed:
        print(f"WARNING: tasks.json was generated with seed {tasks_file['seed']}, --seed is {args.seed}", file=sys.stderr)
    tasks = tasks_file["tasks"][: args.n_tasks]
    for c in args.conditions:
        missing = [t["task_id"] for t in tasks if c != "clean" and c not in t["corruptions"]]
        if missing:
            print(f"condition '{c}' is not defined for tasks {missing[:5]}... in {args.tasks}", file=sys.stderr)
            sys.exit(2)
    proteins = args.proteins or tasks_file.get("proteins")
    table = ProteinTable(proteins, record_format=args.record_format) if proteins else ProteinTable(record_format=args.record_format)
    samples = range(args.sample_start, args.sample_start + args.samples)
    jobs = [(t, c, s) for s in samples for t in tasks for c in args.conditions]

    if len(jobs) > HARD_CAP and not args.yes:
        print(f"Refusing to launch {len(jobs)} runs (> {HARD_CAP}). Re-run with --yes if you really want this.", file=sys.stderr)
        sys.exit(2)

    # The model label stored in traces and cache keys: bare Claude names stay as before so existing
    # cache entries and grade.py filters keep working; other providers keep their 'kind:model' spec.
    model = "mock" if args.mock else args.model
    provider, cfg_for_hash = None, {}
    if not args.mock:
        try:
            provider = make_provider(args.model, system_prompt(args.verify_prompt), tool_schemas(args.record_format),
                                     thinking=args.thinking, effort=args.effort)
            if provider.name == "anthropic":  # preflight: credentials resolve and the model id exists (free call)
                provider.client.models.retrieve(provider.model)
        except Exception as e:
            print(f"Cannot set up model '{args.model}': {type(e).__name__}: {e}\n"
                  "Check the API key for this provider (ANTHROPIC_API_KEY / OPENAI_API_KEY / TOGETHER_API_KEY) and --model.",
                  file=sys.stderr)
            sys.exit(1)
        cfg_for_hash = {k: v for k, v in provider.config().items() if k != "provider"}
    CACHE_DIR.mkdir(exist_ok=True)
    Path(args.out).parent.mkdir(exist_ok=True)

    def one(task, condition, sample):
        phash = prompt_hash(cfg_for_hash, task["prompt"])
        key = cache_key(model, condition, task["task_id"], phash, sample)
        cpath = CACHE_DIR / f"{key}.json"
        cached = False
        if cpath.exists() and not args.no_cache and not args.mock:
            trace, cached = json.loads(cpath.read_text()), True
        else:
            layer = CorruptingToolLayer(table, condition, task)
            if args.mock:
                trace = run_mock_agent(task, layer, args.verify_prompt)
            else:
                trace = run_agent(provider, task, layer)
            if not args.mock and trace["error"] is None:
                cpath.write_text(json.dumps(trace, default=str))
        check_no_leak(trace, task, condition, table)
        implied = task["corruptions"][condition]["implied"] if condition != "clean" else None
        return {
            "run_key": key, "cached": cached, "model": model, "condition": condition, "sample": sample,
            "verify_prompt": args.verify_prompt, "thinking": args.thinking, "effort": args.effort,
            "seed": args.seed, "task_id": task["task_id"], "template": task["template"],
            "target_field": task["target_field"], "target_accession": task["target_accession"],
            "gold": task["gold"], "implied": implied, "answer_type": task["answer_type"],
            "corruption": None if condition == "clean" else task["corruptions"][condition],
            "correct": match_answer(trace["answer"], task["gold"], task["answer_type"]),
            "propagated": (match_answer(trace["answer"], implied, task["answer_type"]) if implied is not None else None),
            "trace": trace,
        }

    print(f"{len(jobs)} runs: {len(tasks)} tasks x {args.conditions} x {args.samples} sample(s)  model={model}  "
          f"verify_prompt={args.verify_prompt}  thinking={args.thinking} effort={args.effort or 'default'}", file=sys.stderr)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex, open(args.out, "a") as fout:
        futs = {ex.submit(one, t, c, s): (t["task_id"], c, s) for t, c, s in jobs}
        for i, f in enumerate(as_completed(futs), 1):
            rec = f.result()
            results.append(rec)
            fout.write(json.dumps(rec, default=str) + "\n")
            fout.flush()
            tr = rec["trace"]
            print(f"  [{i}/{len(jobs)}] {rec['task_id']} {rec['condition']:10s} correct={rec['correct']!s:5s} "
                  f"propagated={rec['propagated']!s:5s} concerns={len(tr['concerns'] or [])} "
                  f"${tr['cost_usd']:.4f}{' (cached)' if rec['cached'] else ''}{' ERROR: ' + tr['error'] if tr['error'] else ''}",
                  file=sys.stderr)

    results.sort(key=lambda r: (r["sample"], r["task_id"], r["condition"]))
    if len(tasks) <= 3 and not args.quiet:
        for rec in results:
            print_trace(rec)

    n_live = sum(1 for r in results if not r["cached"])
    total = sum(r["trace"]["cost_usd"] for r in results)
    per_run = total / len(results) if results else 0.0
    n_full = tasks_file["n_tasks"]
    print("\n--- cost ---")
    print(f"runs: {len(results)} ({n_live} live, {len(results) - n_live} cached)   total this invocation: ${total:.4f}   mean per run: ${per_run:.4f}")
    print(f"estimated full run, {n_full} tasks x {len(args.conditions)} conditions x {args.samples} sample(s) = "
          f"{n_full * len(args.conditions) * args.samples} runs: ${per_run * n_full * len(args.conditions) * args.samples:.2f}")
    n_err = sum(1 for r in results if r["trace"]["error"])
    if n_err:
        print(f"WARNING: {n_err} runs errored (not cached; re-run to retry).", file=sys.stderr)
    n_parse = sum(1 for r in results if not r["trace"]["parsed_ok"] and not r["trace"]["error"])
    if n_parse:
        print(f"WARNING: {n_parse} runs finished but produced no parseable JSON answer.", file=sys.stderr)
    acc = {c: [r["correct"] for r in results if r["condition"] == c] for c in args.conditions}
    print("accuracy by condition:", {c: f"{sum(v)}/{len(v)}" for c, v in acc.items()})
    print(f"traces appended to {args.out}")


if __name__ == "__main__":
    main()
