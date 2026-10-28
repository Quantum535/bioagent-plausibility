#!/bin/zsh
[ -f .env ] && { set -a; source .env; set +a; }
arm() {
  O=results/coherent/harness_ss$3; mkdir -p $O; export HARNESS_SECOND_SOURCE=$3
  python run.py --model $1 --harness annotate --tasks data/coherent_shrink.json --seed 1 --n_tasks 100 --quiet --conditions clean coherent_impossible coherent_plausible --out $O/$2_prot_shrink.jsonl
  python run.py --model $1 --harness annotate --tasks data/coherent_inflate_v2.json --seed 1 --n_tasks 100 --quiet --conditions clean coherent_plausible --out $O/$2_prot_inflate_v2.jsonl
  python run.py --model $1 --harness annotate --tasks data/chem/coherent_shrink.json --n_tasks 100 --quiet --conditions clean coherent_impossible coherent_plausible --out $O/$2_chem_shrink.jsonl
  python run.py --model $1 --harness annotate --tasks data/chem/coherent_inflate.json --n_tasks 100 --quiet --conditions clean coherent_plausible --out $O/$2_chem_inflate.jsonl
}
for S in 0 1; do
  ( arm claude-opus-5 opus5 $S ) > results/coherent/harness_ss${S}_opus5.log 2>&1 &
  ( arm gemini:gemini-4-argon argon $S ) > results/coherent/harness_ss${S}_argon.log 2>&1 &
done
D=together:deepseek-ai/DeepSeek-V4.1-Flash-1017
( arm $D deepseek 0; arm $D deepseek 1; unset HARNESS_SECOND_SOURCE
  python run.py --model $D --harness replace --tasks data/tasks_v2.json --seed 1 --n_tasks 200 --quiet --conditions clean impossible plausible --out results/harness/traces_deepseek_protein_replace.jsonl
  python run.py --model $D --harness replace --tasks data/chem/tasks.json --n_tasks 100 --quiet --conditions clean impossible plausible --out results/harness/traces_deepseek_chem_replace.jsonl
) > results/coherent/harness_ss_deepseek_and_p2replace.log 2>&1 &
wait
echo "harness rerun done $(date)"
