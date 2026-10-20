#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
set -a; source .env; set +a
mkdir -p results/v2_full
run() {
  caffeinate -i python run.py --model "$1" --tasks data/tasks_v2.json --seed 1 --record_format full \
    --n_tasks 100 --quiet --workers "$3" --out "results/v2_full/traces_$2.jsonl"
}
run gemini:gemini-4-argon                          gemini4argon      4
run together:deepseek-ai/DeepSeek-V4.1-Flash-1017  deepseek_v41flash 2
run anthropic:claude-opus-5                        opus5             4
echo "FULL DONE $(date)"
