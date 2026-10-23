import json, os, sys, time, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; OUT = Path(__file__).parent
for line in (ROOT / ".env").read_text().splitlines():            # load API keys from the repo .env
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
from biomni.config import default_config
default_config.temperature = None
# Claude 5 models reject the temperature parameter; strip it from every outgoing request body at the SDK's request builder
import anthropic._base_client as _bc
_orig_build = _bc.BaseClient._build_request
def _build(self, options, *a, **k):
    jd = getattr(options, "json_data", None)
    if isinstance(jd, dict): jd.pop("temperature", None)
    return _orig_build(self, options, *a, **k)
_bc.BaseClient._build_request = _build
print("anthropic request builder patched")
from biomni.agent import A1
tasks = json.load(open(ROOT / "data/tasks_v2.json"))["tasks"][:15] + json.load(open(ROOT / "data/chem/tasks.json"))["tasks"][:10]
agent = A1(path=str(OUT / "biomni_data"), llm="deepseek-ai/DeepSeek-V4.1-Flash-1017", source="Custom", base_url="https://api.together.xyz/v1",
           api_key=os.environ["TOGETHER_API_KEY"], timeout_seconds=600, expected_data_lake_files=[])
for t in tasks:
    log = OUT / f"net_{t['task_id']}.jsonl"; os.environ["NETLOG"] = str(log)
    t0 = time.time()
    try: result = agent.go(t["prompt"])
    except Exception as e: result = f"ERROR {e}\n{traceback.format_exc()[-800:]}"
    (OUT / f"out_{t['task_id']}.json").write_text(json.dumps({"task_id": t["task_id"], "prompt": t["prompt"], "gold": t["gold"],
                                                               "elapsed": time.time() - t0, "result": str(result)}, indent=1))
    n = sum(1 for _ in open(log)) if log.exists() else 0
    print(f"{t['task_id']}  {time.time()-t0:5.0f}s  net lines: {n}", flush=True)
