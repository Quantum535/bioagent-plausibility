#!/bin/bash
# Three background chains, one per provider. Run from the repository root.
cd "$(dirname "$0")/../.." || exit 1
set -a; source .env; set +a   # API keys for the background chains
seed() { python -c "import json,sys; print(json.load(open(sys.argv[1])).get('seed', 0))" "$1"; }
S2=$(seed data/tasks_v2.json); S4=$(seed data/chem/phase4b_C.json); SC=$(seed data/coherent_shrink.json); SCH=$(seed data/chem/tasks.json)
chain() {  # $1 short name, $2 model spec, $3 "full" for all experiments or "agree" for the agreement cells only
  m=$1; M=$2; run() { python run.py --model "$M" --quiet --yes "$@"; }
  for V in no_tool_instruction record_errors two_fields; do
    [ "$3" = full ] && run --tasks data/tasks_v2.json --seed "$S2" --record_format full --n_tasks 100 --conditions plausible --prompt_variant $V --out results/prompt_ablation/${m}_protein_$V.jsonl
    run --tasks data/chem/phase4b_C.json --seed "$S4" --record_format full --n_tasks 60 --samples 3 --conditions plausible --prompt_variant $V --out results/prompt_ablation/${m}_agreeC_$V.jsonl
    [ "$3" = full ] && run --tasks data/coherent_shrink.json --seed "$SC" --record_format full --n_tasks 100 --conditions coherent_plausible --prompt_variant $V --out results/prompt_ablation/${m}_coherent_$V.jsonl
  done
  for A in R0 R1 R2; do run --tasks data/chem/phase4b_$A.json --seed "$S4" --record_format full --n_tasks 60 --samples 3 --conditions plausible --out results/repetition/${m}_$A.jsonl; done
  run --tasks data/chem/phase4b_R1.json --seed "$S4" --record_format full --n_tasks 60 --conditions clean --out results/repetition/${m}_R1_clean.jsonl
  if [ "$3" = full ]; then
    run --tasks data/tasks_v2.json --seed "$S2" --record_format full --n_tasks 100 --harness blank --conditions impossible plausible --out results/blank_harness/${m}_protein.jsonl
    run --tasks data/chem/tasks.json --seed "$SCH" --record_format full --n_tasks 100 --harness blank --conditions impossible plausible --out results/blank_harness/${m}_chem.jsonl
  fi
  echo "CHAIN $m DONE $(date)"
}
WHICH=${1:-all}
[ "$WHICH" = all ] || [ "$WHICH" = opus5 ] && nohup bash -c "$(declare -f seed run chain); S2=$S2; S4=$S4; SC=$SC; SCH=$SCH; chain opus5 anthropic:claude-opus-5 full" >> results/new_experiments/opus5.log 2>&1 &
[ "$WHICH" = all ] || [ "$WHICH" = deepseek ] && nohup bash -c "$(declare -f seed run chain); S2=$S2; S4=$S4; SC=$SC; SCH=$SCH; chain deepseek together:deepseek-ai/DeepSeek-V4.1-Flash-1017 full" >> results/new_experiments/deepseek.log 2>&1 &
[ "$WHICH" = all ] || [ "$WHICH" = vertex ] && nohup bash -c "$(declare -f seed run chain); S2=$S2; S4=$S4; SC=$SC; SCH=$SCH; chain argon gemini:gemini-4-argon full; chain flash gemini:gemini-3.8-flash agree" >> results/new_experiments/vertex.log 2>&1 &
sleep 3; echo "chains started: $(pgrep -f 'chain ' | wc -l)"
