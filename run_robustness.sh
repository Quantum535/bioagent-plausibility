#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
S=$(python run.py --help | grep -oE -- '--n_samples|--samples' | head -n 1)
[ -n "$S" ] || { echo "no samples flag found in run.py"; exit 1; }
T5=data/phase5_tasks.json; O=results/robustness; mkdir -p $O
p5() {
  HARNESS_SECOND_SOURCE=1 python run.py --model $2 --harness replace --tasks $T5 --seed 1 --n_tasks 100 --quiet --conditions clean --out $O/$1_p5_replace.jsonl
  HARNESS_SECOND_SOURCE=1 python run.py --model $2 --harness replace --tasks $T5 --seed 1 --n_tasks 100 $S 3 --quiet --conditions superseded --out $O/$1_p5_replace.jsonl
  HARNESS_SECOND_SOURCE=1 python run.py --model $2 --harness annotate --tasks $T5 --seed 1 --n_tasks 100 $S 3 --quiet --conditions superseded --out $O/$1_p5_annotate.jsonl
  python run.py --model $2 --tasks $T5 --seed 1 --record_format full --n_tasks $3 $S 3 --quiet --conditions superseded --out $O/$1_p5_full.jsonl
}
p4b() {
  for X in A B C; do python run.py --model $2 --tasks data/chem/phase4b_$X.json --seed 4 --record_format full --n_tasks 60 $S 3 --quiet --conditions plausible --out $O/$1_4b_$X.jsonl; done
  python run.py --model $2 --tasks data/chem/phase4_mono.json --seed 4 --record_format full --n_tasks 60 $S 3 --quiet --conditions plausible --out $O/$1_4b_P4.jsonl
}
D=together:deepseek-ai/DeepSeek-V4.1-Flash-1017
( p5 opus5 claude-opus-5 30; p4b opus5 claude-opus-5 ) > $O/opus5.log 2>&1 &
( p5 argon gemini:gemini-4-argon 100; p4b argon gemini:gemini-4-argon ) > $O/argon.log 2>&1 &
( p4b flash gemini:gemini-3.8-flash ) > $O/flash.log 2>&1 &
( p5 deepseek $D 100; p4b deepseek $D ) > $O/deepseek.log 2>&1 &
wait
echo "robustness done $(date)"
