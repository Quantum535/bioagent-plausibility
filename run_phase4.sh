#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
T=data/chem/phase4_tasks.json; O=results/phase4
for P in opus5=claude-opus-5 sonnet5=claude-sonnet-5 argon=gemini:gemini-4-argon flash=gemini:gemini-3.8-flash deepseek=together:deepseek-ai/DeepSeek-V4.1-Flash-1017; do N=${P%%=*}; M=${P#*=}; (
  python run.py --model $M --tasks $T --seed 4 --record_format full --n_tasks 180 --quiet --conditions clean impossible plausible --out $O/${N}_full.jsonl
  python run.py --model $M --tasks $T --seed 4 --n_tasks 180 --quiet --conditions clean impossible plausible --out $O/${N}_summary.jsonl
) > $O/${N}.log 2>&1 & done
wait
echo "phase 4 done $(date)"
