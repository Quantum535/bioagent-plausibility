import json

from openai import OpenAI

from providers.base import Provider, Turn, ToolCall


class OpenAICompatProvider(Provider):
    def __init__(self, model, system, tools, base_url=None, api_key=None, reasoning_effort=None,
                 max_tokens=8000, name="openai", price=(2.0, 10.0, 0.2)):
        self.client = OpenAI(base_url=base_url, api_key=api_key, max_retries=8)
        self.name, self.model, self.system = name, model, system
        self.tools = [{"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
            for t in tools]
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self._price = price

    def config(self):
        return {"provider": self.name, "model": self.model, "system": self.system,
                "tools": self.tools, "max_tokens": self.max_tokens,
                "reasoning_effort": self.reasoning_effort}

    def price(self):
        return self._price

    def user_msg(self, text):
        return {"role": "user", "content": text}

    def complete(self, history, force_no_tools=False):
        kwargs = dict(
            model=self.model,
            tools=self.tools,
            messages=[{"role": "system", "content": self.system}] + history,
            max_completion_tokens=self.max_tokens,
            tool_choice="none" if force_no_tools else "auto",
        )
        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        calls = [ToolCall(tc.id, tc.function.name, json.loads(tc.function.arguments or "{}"))
                 for tc in (msg.tool_calls or [])]
        u = resp.usage
        details = getattr(u, "prompt_tokens_details", None)
        cached = (getattr(details, "cached_tokens", 0) or 0) if details else 0
        return Turn(
            text=msg.content or "",
            tool_calls=calls,
            stop="tool_use" if calls else resp.choices[0].finish_reason,
            usage={"input_tokens": u.prompt_tokens - cached,
                   "output_tokens": u.completion_tokens,
                   "cached_input_tokens": cached},
            raw=msg.model_dump(),
            assistant_msg=msg.model_dump(exclude_none=True),
        )

    def tool_result_msg(self, calls, outputs, extra_text=None):
        msgs = [{"role": "tool", "tool_call_id": c.id, "content": out}
                for c, (out, _) in zip(calls, outputs)]
        if extra_text:
            msgs.append({"role": "user", "content": extra_text})
        return msgs
