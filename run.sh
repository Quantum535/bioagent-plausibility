#!/usr/bin/env bash
# Full reproduction. Requires ANTHROPIC_API_KEY (or an `ant auth login` profile) for the run.py steps.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
if [ -f .env ]; then set -a; . ./.env; set +a; fi   # optional: ANTHROPIC_API_KEY=... in .env
export MODEL=${MODEL:-claude-sonnet-5}

$PY fetch_data.py --seed 0
$PY make_tasks.py --seed 0 --n_tasks 40
$PY run.py --conditions clean impossible plausible --n_tasks 3        # smoke test: prints 9 traces + cost estimate
$PY run.py --conditions clean impossible plausible --n_tasks 40 --quiet
$PY run.py --conditions clean impossible plausible --n_tasks 40 --quiet --verify_prompt   # optional 4th condition
$PY grade.py
# Extended experiment (more samples, more models, plausibility sweep): ./run_extended.sh && $PY grade.py && $PY grade_sweep.py
