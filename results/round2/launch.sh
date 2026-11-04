#!/bin/bash
# Round 2 runs: three provider chains. Usage: bash results/round2/launch.sh
cd "$(dirname "$0")/../.." || exit 1
set -a; source .env; set +a
S2=$(python -c "import json; print(json.load(open('data/tasks_v2.json'))['seed'])")
S5=$(python -c "import json; print(json.load(open('data/phase5_tasks.json'))['seed'])")
SC=$(python -c "import json; print(json.load(open('data/chem/tasks.json'))['seed'])")
O=results/round2
run() { python run.py --quiet --yes "$@" >> "$O/run.log" 2>&1; }
chain() {  # $1 model id, $2 short name, $3 which arms (all|fd|th)
  M=$1; m=$2
  if [ "$3" != "fd" ]; then
    run --model "$M" --tasks data/phase5_tasks.json --seed "$S5" --record_format anonymous --n_tasks 79 --conditions superseded --out "$O/${m}_IS_hist.jsonl"
    run --model "$M" --tasks data/tasks_v2_lenthresh.json --seed "$S2" --record_format anonymous --n_tasks 25 --conditions clean impossible plausible --samples 3 --out "$O/${m}_IS_bench.jsonl"
    run --model "$M" --tasks data/tasks_v2.json --seed "$S2" --prompt_variant no_concerns --n_tasks 100 --conditions impossible plausible --out "$O/${m}_NC_protein.jsonl"
    run --model "$M" --tasks data/chem/tasks.json --seed "$SC" --prompt_variant no_concerns --n_tasks 100 --conditions impossible plausible --out "$O/${m}_NC_chem.jsonl"
  fi
  run --model "$M" --tasks data/chem/phase4b_F1.json --seed 4 --record_format full --n_tasks 60 --conditions clean plausible --out "$O/${m}_F1.jsonl"
  run --model "$M" --tasks data/chem/phase4b_F2.json --seed 4 --record_format full --n_tasks 60 --conditions plausible --out "$O/${m}_F2.jsonl"
  if [ "$3" = "th" ]; then
    run --model "$M" --tasks data/tasks_v2.json --seed "$S2" --record_format full --thinking disabled --n_tasks 50 --conditions impossible plausible --out "$O/${m}_TH_full.jsonl"
    run --model anthropic:claude-sonnet-5 --tasks data/tasks_v2.json --seed "$S2" --thinking disabled --n_tasks 200 --conditions impossible plausible --out "$O/sonnet5_TH_protein.jsonl"
    run --model anthropic:claude-sonnet-5 --tasks data/chem/tasks.json --seed "$SC" --thinking disabled --n_tasks 100 --conditions impossible plausible --out "$O/sonnet5_TH_chem.jsonl"
  fi
  echo "chain $m done $(date)" >> "$O/run.log"
}
nohup bash -c "$(declare -f run chain); O=$O; S2=$S2; S5=$S5; SC=$SC; chain anthropic:claude-opus-5 opus5 th" > /dev/null 2>&1 &
nohup bash -c "$(declare -f run chain); O=$O; S2=$S2; S5=$S5; SC=$SC; chain gemini:gemini-4-argon argon all; chain gemini:gemini-3.8-flash flash fd" > /dev/null 2>&1 &
nohup bash -c "$(declare -f run chain); O=$O; S2=$S2; S5=$S5; SC=$SC; chain together:deepseek-ai/DeepSeek-V4.1-Flash-1017 deepseek all" > /dev/null 2>&1 &
echo "launched three chains; progress: tail -n 3 $O/run.log; ls $O/*.jsonl"
