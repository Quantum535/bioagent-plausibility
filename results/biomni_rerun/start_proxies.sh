#!/bin/bash
# One proxy per shard; each line explicit. Run from the repository root.
cd "$(dirname "$0")/../.." || exit 1
pkill -f mitmdump; sleep 1
start() { PROXYLOG=results/biomni_rerun/proxy_$1_$2.jsonl AGENT_STATE=/Users/Shared/agentrun/state/current_$1_$2.json RERUN_SCHEDULE=harness/rerun_schedule.json \
          nohup /opt/homebrew/bin/mitmdump -p "$3" -s harness/corrupt_proxy.py > "results/biomni_rerun/mitm_$1_$2.log" 2>&1 & }
start flash 0 8899; start flash 1 8900; start deepseek 0 8901; start deepseek 1 8902
sleep 4
for port in 8899 8900 8901 8902; do lsof -nP -iTCP:$port -sTCP:LISTEN | grep -q mitmdump && echo "proxy listening on $port" || echo "NOT LISTENING on $port"; done
