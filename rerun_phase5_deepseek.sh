#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
T=data/phase5_tasks.json; O=results/phase5; M=together:deepseek-ai/DeepSeek-V4.1-Flash-1017
python run.py --model $M --tasks $T --seed 1 --record_format full --n_tasks 100 --quiet --conditions clean superseded --out $O/deepseek_full.jsonl
python run.py --model $M --tasks $T --seed 1 --n_tasks 100 --quiet --conditions clean superseded --out $O/deepseek_summary.jsonl
HARNESS_SECOND_SOURCE=1 python run.py --model $M --harness annotate --tasks $T --seed 1 --n_tasks 100 --quiet --conditions clean superseded --out $O/deepseek_harness_ss1.jsonl
echo "deepseek phase 5 done $(date)"
