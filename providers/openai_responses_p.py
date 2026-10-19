from openai import OpenAI

from providers.base import Provider, Turn, ToolCall


class OpenAIResponsesProvider(Provider):
    """OpenAI reasoning models via the Responses API. Conversation state is carried by
    previous_response_id, which also preserves hidden reasoning across tool rounds."""
    name = "openai"

    def __init__(self, model, system, tools, reasoning_effort=None, max_tokens=8000,
                 price=(2.0, 10.0, 0.2)):
        self.client = OpenAI(max_retries=8)
        self.model, self.system = model, system
        self.tools = [{"type": "function", "name": t["name"], "description": t["description"],
                       "parameters": t["input_schema"]} for t in tools]
        self.max_tokens, self.reasoning_effort, self._price = max_tokens, reasoning_effort, price

    def config(self):
        return {"provider": self.name, "api": "responses", "model": self.model, "system": self.system,
                "tools": self.tools, "max_tokens": self.max_tokens, "reasoning_effort": self.reasoning_effort}

    def price(self):
        return self._price

    def user_msg(self, text):
        return {"role": "user", "content": text}

    def complete(self, history, force_no_tools=False):
        # history: [user_msg, {"response_id":...}, <function_call_output items...>, {"response_id":...}, ...]
        last = max((i for i, h in enumerate(history) if "response_id" in h), default=-1)
        prev_id = history[last]["response_id"] if last >= 0 else None
        inp = history[last + 1:] if last >= 0 else [history[0]]
        kwargs = dict(model=self.model, instructions=self.system, tools=self.tools, input=inp,
                      max_output_tokens=self.max_tokens, store=True,
                      tool_choice="none" if force_no_tools else "auto")
        if prev_id:
            kwargs["previous_response_id"] = prev_id
        if self.reasoning_effort:
            kwargs["reasoning"] = {"effort": self.reasoning_effort}
        resp = self.client.responses.create(**kwargs)
        calls, texts = [], []
        for item in resp.output:
            if item.type == "function_call":
                import json
                calls.append(ToolCall(item.call_id, item.name, json.loads(item.arguments or "{}")))
            elif item.type == "message":
                for c in item.content:
                    if getattr(c, "type", "") == "output_text":
                        texts.append(c.text)
        u = resp.usage
        cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
        if calls:
            stop = "tool_use"
        elif resp.status == "incomplete":
            stop = "length" if (resp.incomplete_details and resp.incomplete_details.reason == "max_output_tokens") else "incomplete"
        else:
            stop = "stop"
        return Turn(
            text="".join(texts), tool_calls=calls, stop=stop,
            usage={"input_tokens": u.input_tokens - cached, "output_tokens": u.output_tokens,
                   "cached_input_tokens": cached},
            raw=[item.model_dump() for item in resp.output],
            assistant_msg={"response_id": resp.id},
        )

    def tool_result_msg(self, calls, outputs, extra_text=None):
        msgs = [{"type": "function_call_output", "call_id": c.id, "output": out}
                for c, (out, _) in zip(calls, outputs)]
        if extra_text:
            msgs.append({"role": "user", "content": extra_text})
        return msgs
