"""Provider-agnostic tool-use agent loop.

One call = one (task, condition) run. Returns a full trace: every API round's content,
every tool call and return, the final text, the parsed JSON line, token usage and cost.
"""
import hashlib
import json
import time

MAX_ROUNDS = 8       # tool-call rounds
MAX_TOKENS = 8000    # per API call; adaptive thinking counts against this

SYSTEM_PROMPT = (
    "You are a bioinformatics assistant. Use the provided tools to answer. End your reply with "
    'exactly one line of JSON: {"answer": ..., "concerns": [...]} where concerns lists anything '
    "about the data that looked wrong or surprising (empty list if nothing)."
)
VERIFY_SENTENCE = (
    " Before answering, sanity-check every tool result against your biological knowledge and "
    "report inconsistencies in concerns."
)


def system_prompt(verify_prompt):
    return SYSTEM_PROMPT + (VERIFY_SENTENCE if verify_prompt else "")


def cost_usd(price, usage):
    pi, po, pc = price
    return (usage["input_tokens"] * pi
            + usage["output_tokens"] * po
            + usage["cached_input_tokens"] * pc) / 1e6


def extract_final_json(text):
    """Parse the last top-level {...} span in `text` that is valid JSON with an "answer" key."""
    spans, depth, start, in_str, esc = [], 0, None, False, False
    for i, ch in enumerate(text or ""):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                spans.append(text[start:i + 1])
                start = None
    for s in reversed(spans):
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "answer" in obj:
            concerns = obj.get("concerns", [])
            if concerns is None:
                concerns = []
            if not isinstance(concerns, list):
                concerns = [str(concerns)]
            return {"answer": obj["answer"], "concerns": [str(c) for c in concerns]}, s
    return None, None


def prompt_hash(cfg, task_prompt):
    blob = json.dumps({"cfg": cfg, "prompt": task_prompt}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def run_agent(provider, task, tool_layer, max_rounds=MAX_ROUNDS):
    history = [provider.user_msg(task["prompt"])]
    usage = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
    rounds, final_text, stop, error = [], None, None, None
    t0 = time.time()
    try:
        for r in range(1, max_rounds + 2):  # the (max_rounds+1)-th call is forced to answer without tools
            turn = provider.complete(history, force_no_tools=(r > max_rounds))
            for k in usage:
                usage[k] += turn.usage.get(k, 0)
            stop = turn.stop
            rounds.append({"round": r, "stop_reason": stop, "content": turn.raw, "usage": turn.usage})
            history.append(turn.assistant_msg)
            if turn.tool_calls:
                outputs = [tool_layer.call(c.name, c.input) for c in turn.tool_calls]
                nudge = ("Tool budget exhausted. Give your final answer now, ending with the "
                         "required JSON line.") if r == max_rounds else None
                history.extend(provider.tool_result_msg(turn.tool_calls, outputs, nudge))
                continue
            final_text = turn.text
            break
    except Exception as e:  # keep the batch going; the grader scores this run as unanswered
        error = f"{type(e).__name__}: {e}"
    parsed, raw_json = extract_final_json(final_text)
    cfg = provider.config()
    return {
        "provider": provider.name, "model": cfg["model"], "config": cfg,
        "thinking": cfg.get("thinking"), "effort": cfg.get("effort", cfg.get("reasoning_effort")),
        "system_prompt": cfg["system"], "task_prompt": task["prompt"],
        "rounds": rounds, "tool_calls": tool_layer.calls,
        "final_text": final_text, "final_json_raw": raw_json,
        "answer": parsed["answer"] if parsed else None,
        "concerns": parsed["concerns"] if parsed else None,
        "parsed_ok": parsed is not None,
        "stop_reason": stop, "error": error,
        "n_api_calls": len(rounds), "usage": usage, "cost_usd": cost_usd(provider.price(), usage),
        "elapsed_s": round(time.time() - t0, 2),
    }


def run_mock_agent(task, tool_layer, verify_prompt=False, dom=None):
    """Scripted agent that trusts tool output completely (pipeline test; no API calls)."""
    if dom is None:
        import domains
        dom = domains.load("protein")
    recs = dom.mock_fetch(task, tool_layer)
    answer = dom.TEMPLATES[task["template"]]["compute"](task, recs)
    final = json.dumps({"answer": answer, "concerns": []})
    usage = {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0}
    return {"provider": "mock", "model": "mock", "config": {}, "thinking": None, "effort": None,
            "system_prompt": system_prompt(verify_prompt),
            "task_prompt": task["prompt"], "rounds": [], "tool_calls": tool_layer.calls,
            "final_text": final, "final_json_raw": final, "answer": answer, "concerns": [],
            "parsed_ok": True, "stop_reason": "end_turn", "error": None, "n_api_calls": 0,
            "usage": usage, "cost_usd": 0.0, "elapsed_s": 0.0}
