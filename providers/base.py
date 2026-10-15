from dataclasses import dataclass


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class Turn:
    text: str
    tool_calls: list
    stop: str
    usage: dict
    raw: object
    assistant_msg: object


class Provider:
    name = "base"

    def config(self):
        raise NotImplementedError

    def user_msg(self, text):
        raise NotImplementedError

    def complete(self, history, force_no_tools=False):
        raise NotImplementedError

    def tool_result_msg(self, calls, outputs, extra_text=None):
        raise NotImplementedError

    def price(self):
        raise NotImplementedError  # (input $/M, output $/M, cached-input $/M)
