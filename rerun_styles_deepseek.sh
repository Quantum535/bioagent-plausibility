#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
S=$(python run.py --help | grep -oE -- '--n_samples|--samples' | head -n 1)
T5=data/phase5_tasks.json; O=results/robustness; M=together:deepseek-ai/DeepSeek-V4.1-Flash-1017; export HARNESS_SECOND_SOURCE=1
for ST in labeled silent; do
  export HARNESS_REPLACE_STYLE=$ST
  python run.py --model $M --harness replace --tasks $T5 --seed 1 --n_tasks 20 --quiet --conditions clean --out $O/deepseek_p5_replace_$ST.jsonl
  python run.py --model $M --harness replace --tasks $T5 --seed 1 --n_tasks 100 $S 3 --quiet --conditions superseded --out $O/deepseek_p5_replace_$ST.jsonl
done
echo "deepseek styles done $(date)"
