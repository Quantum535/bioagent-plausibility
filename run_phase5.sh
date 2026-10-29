#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
T=data/phase5_tasks.json; O=results/phase5; mkdir -p $O
for P in opus5=claude-opus-5 argon=gemini:gemini-4-argon deepseek=together:deepseek-ai/DeepSeek-V4.1-Flash-1017; do N=${P%%=*}; M=${P#*=}; (
  if [ $N = opus5 ]; then
    python run.py --model $M --tasks $T --seed 1 --record_format full --n_tasks 100 --quiet --conditions superseded --out $O/${N}_full.jsonl
    python run.py --model $M --tasks $T --seed 1 --record_format full --n_tasks 20 --quiet --conditions clean --out $O/${N}_full.jsonl
  else
    python run.py --model $M --tasks $T --seed 1 --record_format full --n_tasks 100 --quiet --conditions clean superseded --out $O/${N}_full.jsonl
  fi
  python run.py --model $M --tasks $T --seed 1 --n_tasks 100 --quiet --conditions clean superseded --out $O/${N}_summary.jsonl
  HARNESS_SECOND_SOURCE=1 python run.py --model $M --harness annotate --tasks $T --seed 1 --n_tasks 100 --quiet --conditions clean superseded --out $O/${N}_harness_ss1.jsonl
) > $O/${N}.log 2>&1 & done
wait
echo "phase 5 done $(date)"
