#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
python run.py --model claude-opus-5 --tasks data/coherent_inflate_v2.json --seed 1 --record_format full --n_tasks 100 --quiet --conditions coherent_plausible --out results/coherent/opus5_prot_inflate_v2.jsonl > results/coherent/dead_opus5_v2.log 2>&1 &
python run.py --model gemini:gemini-4-argon --tasks data/coherent_inflate.json --seed 1 --record_format full --n_tasks 100 --quiet --conditions clean coherent_plausible --out results/coherent/argon_prot_inflate.jsonl > results/coherent/dead_argon_v1.log 2>&1 &
python run.py --model together:deepseek-ai/DeepSeek-V4.1-Flash-1017 --tasks data/coherent_inflate_v2.json --seed 1 --record_format full --n_tasks 100 --quiet --conditions coherent_plausible --out results/coherent/deepseek_prot_inflate_v2.jsonl > results/coherent/dead_deepseek_v2.log 2>&1 &
wait
echo "dead baselines done $(date)"
