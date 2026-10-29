#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
S=$(python run.py --help | grep -oE -- '--n_samples|--samples' | head -n 1)
T5=data/phase5_tasks.json; O=results/robustness; export HARNESS_SECOND_SOURCE=1
arm() {
  export HARNESS_REPLACE_STYLE=$3
  python run.py --model $2 --harness replace --tasks $T5 --seed 1 --n_tasks 20 --quiet --conditions clean --out $O/$1_p5_replace_$3.jsonl
  python run.py --model $2 --harness replace --tasks $T5 --seed 1 --n_tasks 100 $S 3 --quiet --conditions superseded --out $O/$1_p5_replace_$3.jsonl
}
for P in opus5=claude-opus-5 argon=gemini:gemini-4-argon; do N=${P%%=*}; M=${P#*=}; ( arm $N $M labeled; arm $N $M silent ) > $O/styles_$N.log 2>&1 & done
D=together:deepseek-ai/DeepSeek-V4.1-Flash-1017
( arm deepseek $D labeled; arm deepseek $D silent ) > $O/styles_deepseek.log 2>&1 &
wait
echo "replace styles done $(date)"
