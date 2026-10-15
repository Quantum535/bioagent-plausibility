#!/usr/bin/env bash
# Extended experiment: repeated samples, three extra models, and the plausibility sweep.
# Three streams run in parallel; each stream appends to its own trace file. ~1,500 runs, ~$25.
set -uo pipefail
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
if [ -f .env ]; then set -a; . ./.env; set +a; fi
W=${WORKERS:-4}
SWEEP_CONDS=$($PY -c "import json;print(' '.join(['clean']+list(json.load(open('data/sweep_tasks.json'))['tasks'][0]['corruptions'])))")

stream_a() {  # Sonnet 5: two more samples of the main experiment, then the sweep
  $PY run.py --n_tasks 40 --samples 2 --sample_start 1 --quiet --workers $W --out results/traces.jsonl
  $PY run.py --n_tasks 40 --samples 2 --sample_start 1 --quiet --workers $W --out results/traces.jsonl --verify_prompt
  $PY run.py --tasks data/sweep_tasks.json --conditions $SWEEP_CONDS --n_tasks 20 --quiet --workers $W --out results/sweep_traces_sonnet5.jsonl
}
stream_b() {  # Haiku 4.5 main + verify + sweep, then Sonnet 4.6 main + verify
  $PY run.py --model claude-haiku-4-5 --n_tasks 40 --quiet --workers $W --out results/traces_haiku45.jsonl
  $PY run.py --model claude-haiku-4-5 --n_tasks 40 --quiet --workers $W --out results/traces_haiku45.jsonl --verify_prompt
  $PY run.py --model claude-haiku-4-5 --tasks data/sweep_tasks.json --conditions $SWEEP_CONDS --n_tasks 20 --quiet --workers $W --out results/sweep_traces_haiku45.jsonl
  $PY run.py --model claude-sonnet-4-6 --n_tasks 40 --quiet --workers $W --out results/traces_sonnet46.jsonl
  $PY run.py --model claude-sonnet-4-6 --n_tasks 40 --quiet --workers $W --out results/traces_sonnet46.jsonl --verify_prompt
}
stream_c() {  # Opus 5 main + verify + sweep
  $PY run.py --model claude-opus-5 --n_tasks 40 --quiet --workers $W --out results/traces_opus5.jsonl
  $PY run.py --model claude-opus-5 --n_tasks 40 --quiet --workers $W --out results/traces_opus5.jsonl --verify_prompt
  $PY run.py --model claude-opus-5 --tasks data/sweep_tasks.json --conditions $SWEEP_CONDS --n_tasks 20 --quiet --workers $W --out results/sweep_traces_opus5.jsonl
}

stream_a > results/logs/stream_a.log 2>&1 &
stream_b > results/logs/stream_b.log 2>&1 &
stream_c > results/logs/stream_c.log 2>&1 &
wait
echo "ALL STREAMS DONE $(date)" | tee results/logs/extended.done
