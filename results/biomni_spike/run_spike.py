import json, os, sys, time, traceback
from pathlib import Path
import anthropic._base_client as _bc
_seen = []
def _patch(cls):
    orig = cls.post
    def post(self, path, *a, **k):
        b = k.get("body")
        if isinstance(b, dict) and "temperature" in b:
            b.pop("temperature")
            if not _seen: _seen.append(1); print("[patch] stripped temperature on", path)
        return orig(self, path, *a, **k)
    cls.post = post
_patch(_bc.SyncAPIClient); _patch(_bc.AsyncAPIClient)
from biomni.agent import A1
OUT = Path("results/biomni_spike"); LOG = OUT / "net.jsonl"
os.environ["NETLOG"] = str(LOG)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 25
tasks = (json.load(open("data/tasks_v2.json"))["tasks"][:15] + json.load(open("data/chem/tasks.json"))["tasks"][:10])[:N]
agent = A1(path=str(OUT / "biomni_data"), llm="claude-sonnet-5", source="Anthropic", timeout_seconds=600, expected_data_lake_files=[])
for t in tasks:
    with open(LOG, "a") as f: f.write(json.dumps({"kind": "task_start", "task_id": t["task_id"], "t": time.time()}) + "\n")
    t0 = time.time()
    try: result = agent.go(t["prompt"])
    except Exception as e: result = f"ERROR {e}\n{traceback.format_exc()[-800:]}"
    (OUT / f"out_{t['task_id']}.json").write_text(json.dumps({"task_id": t["task_id"], "prompt": t["prompt"], "gold": t["gold"], "elapsed": round(time.time()-t0), "result": str(result)}, indent=1))
    print(t["task_id"], f"{time.time()-t0:.0f}s")
