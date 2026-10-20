#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
set -a; source .env; set +a
mkdir -p results/v2
run() {  # $1 = model spec, $2 = output slug, $3 = workers
  for v in "" "--verify_prompt"; do
    caffeinate -i python run.py --model "$1" --tasks data/tasks_v2.json --seed 1 --n_tasks 200 --quiet --workers "$3" \
      --out "results/v2/traces_$2.jsonl" $v
  done
}
run anthropic:claude-sonnet-5                          sonnet5        4
run anthropic:claude-opus-5                            opus5          4
run gemini:gemini-4-argon                              gemini4argon   4
run openai:gpt-6.1-sol                                 gpt61sol       4
run together:deepseek-ai/DeepSeek-V4.1-Flash-1017      deepseek_v41flash 2
run together:moonshotai/Kimi-K3                        kimi_k3        2
run gemini:gemini-3.8-flash                            gemini38flash  4
run openai:gpt-6-luna                                  gpt6luna       4
run anthropic:claude-sonnet-4-6                        sonnet46       4
run anthropic:claude-haiku-4-5                         haiku45        4
echo "V2 DONE $(date)"
