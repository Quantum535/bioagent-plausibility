#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
run() { python run.py --model together:deepseek-ai/DeepSeek-V4.1-Flash-1017 --n_tasks 100 --quiet "$@"; }
R=results/coherent
run --tasks data/coherent_shrink.json --seed 1 --record_format full --conditions clean coherent_impossible coherent_plausible --out $R/deepseek_prot_shrink.jsonl
run --tasks data/coherent_inflate.json --seed 1 --record_format full --conditions clean coherent_plausible --out $R/deepseek_prot_inflate.jsonl
run --tasks data/coherent_inflate_v2.json --seed 1 --record_format full --conditions coherent_plausible --out $R/deepseek_prot_inflate_v2.jsonl
run --tasks data/chem/coherent_shrink.json --record_format full --conditions clean coherent_impossible coherent_plausible --out $R/deepseek_chem_shrink.jsonl
run --tasks data/chem/coherent_inflate.json --record_format full --conditions clean coherent_plausible --out $R/deepseek_chem_inflate.jsonl
for S in 0 1; do
  export HARNESS_SECOND_SOURCE=$S; O=$R/harness_ss$S
  run --harness annotate --tasks data/coherent_shrink.json --seed 1 --conditions clean coherent_impossible coherent_plausible --out $O/deepseek_prot_shrink.jsonl
  run --harness annotate --tasks data/coherent_inflate_v2.json --seed 1 --conditions clean coherent_plausible --out $O/deepseek_prot_inflate_v2.jsonl
  run --harness annotate --tasks data/chem/coherent_shrink.json --conditions clean coherent_impossible coherent_plausible --out $O/deepseek_chem_shrink.jsonl
  run --harness annotate --tasks data/chem/coherent_inflate.json --conditions clean coherent_plausible --out $O/deepseek_chem_inflate.jsonl
done
unset HARNESS_SECOND_SOURCE; O=$R/summary_noharness; mkdir -p $O
run --tasks data/coherent_shrink.json --seed 1 --conditions clean coherent_impossible coherent_plausible --out $O/deepseek_prot_shrink.jsonl
run --tasks data/coherent_inflate_v2.json --seed 1 --conditions clean coherent_plausible --out $O/deepseek_prot_inflate_v2.jsonl
run --tasks data/chem/coherent_shrink.json --conditions clean coherent_impossible coherent_plausible --out $O/deepseek_chem_shrink.jsonl
run --tasks data/chem/coherent_inflate.json --conditions clean coherent_plausible --out $O/deepseek_chem_inflate.jsonl
echo "deepseek done $(date)"
