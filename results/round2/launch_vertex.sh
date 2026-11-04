#!/bin/bash
cd "$(dirname "$0")/../.." || exit 1
set -a; source .env; set +a
S2=$(python -c "import json; print(json.load(open('data/tasks_v2.json'))['seed'])")
S5=$(python -c "import json; print(json.load(open('data/phase5_tasks.json'))['seed'])")
SC=$(python -c "import json; print(json.load(open('data/chem/tasks.json'))['seed'])")
O=results/round2
run() { python run.py --quiet --yes "$@" >> "$O/run.log" 2>&1; }
M=gemini:gemini-4-argon; m=argon
run --model "$M" --tasks data/phase5_tasks.json --seed "$S5" --record_format anonymous --n_tasks 79 --conditions superseded --out "$O/${m}_IS_hist.jsonl"
run --model "$M" --tasks data/tasks_v2_lenthresh.json --seed "$S2" --record_format anonymous --n_tasks 25 --conditions clean impossible plausible --samples 3 --out "$O/${m}_IS_bench.jsonl"
run --model "$M" --tasks data/tasks_v2.json --seed "$S2" --prompt_variant no_concerns --n_tasks 100 --conditions impossible plausible --out "$O/${m}_NC_protein.jsonl"
run --model "$M" --tasks data/chem/tasks.json --seed "$SC" --prompt_variant no_concerns --n_tasks 100 --conditions impossible plausible --out "$O/${m}_NC_chem.jsonl"
run --model "$M" --tasks data/chem/phase4b_F1.json --seed 4 --record_format full --n_tasks 60 --conditions clean plausible --out "$O/${m}_F1.jsonl"
run --model "$M" --tasks data/chem/phase4b_F2.json --seed 4 --record_format full --n_tasks 60 --conditions plausible --out "$O/${m}_F2.jsonl"
M=gemini:gemini-3.8-flash; m=flash
run --model "$M" --tasks data/chem/phase4b_F1.json --seed 4 --record_format full --n_tasks 60 --conditions clean plausible --out "$O/${m}_F1.jsonl"
run --model "$M" --tasks data/chem/phase4b_F2.json --seed 4 --record_format full --n_tasks 60 --conditions plausible --out "$O/${m}_F2.jsonl"
echo "chain vertex done $(date)" >> "$O/run.log"
