#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
[ -f data/coherent_inflate_v2.json ] || { echo "missing data/coherent_inflate_v2.json"; exit 1; }
for P in opus5=claude-opus-5 argon=gemini:gemini-4-argon deepseek=together:deepseek-ai/DeepSeek-V4.1-Flash-1017; do N=${P%%=*}; M=${P#*=}; for S in 0 1; do mkdir -p results/coherent/harness_ss$S; (
  export HARNESS_SECOND_SOURCE=$S; O=results/coherent/harness_ss$S
  [ $S = 0 ] && python run.py --model $M --tasks data/coherent_inflate_v2.json --seed 1 --record_format full --n_tasks 100 --quiet --conditions coherent_plausible --out results/coherent/${N}_prot_inflate_v2.jsonl
  python run.py --model $M --harness annotate --tasks data/coherent_shrink.json --seed 1 --n_tasks 100 --quiet --conditions clean coherent_impossible coherent_plausible --out $O/${N}_prot_shrink.jsonl
  python run.py --model $M --harness annotate --tasks data/coherent_inflate_v2.json --seed 1 --n_tasks 100 --quiet --conditions clean coherent_plausible --out $O/${N}_prot_inflate_v2.jsonl
  python run.py --model $M --harness annotate --tasks data/chem/coherent_shrink.json --n_tasks 100 --quiet --conditions clean coherent_impossible coherent_plausible --out $O/${N}_chem_shrink.jsonl
  python run.py --model $M --harness annotate --tasks data/chem/coherent_inflate.json --n_tasks 100 --quiet --conditions clean coherent_plausible --out $O/${N}_chem_inflate.jsonl
) > results/coherent/harness_ss${S}_${N}.log 2>&1 & done; done
sleep 5
while pgrep -f "run.py --model" >/dev/null; do sleep 30; done
echo "all Phase 3 runs finished $(date)"
