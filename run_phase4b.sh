#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
O=results/phase4b; mkdir -p $O
for P in opus5=claude-opus-5 sonnet5=claude-sonnet-5 argon=gemini:gemini-4-argon flash=gemini:gemini-3.8-flash deepseek=together:deepseek-ai/DeepSeek-V4.1-Flash-1017; do N=${P%%=*}; M=${P#*=}; (
  python run.py --model $M --tasks data/chem/phase4b_A.json --seed 4 --record_format full --n_tasks 60 --quiet --conditions clean plausible --out $O/${N}_A.jsonl
  python run.py --model $M --tasks data/chem/phase4b_B.json --seed 4 --record_format full --n_tasks 60 --quiet --conditions clean plausible --out $O/${N}_B.jsonl
  python run.py --model $M --tasks data/chem/phase4b_C.json --seed 4 --record_format full --n_tasks 60 --quiet --conditions plausible --out $O/${N}_C.jsonl
) > $O/${N}.log 2>&1 & done
wait
echo "phase 4b done $(date)"
