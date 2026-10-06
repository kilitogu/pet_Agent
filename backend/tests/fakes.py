"""伪造 OpenAI 客户端：按脚本依次返回预设响应，用于完全离线地驱动 Agent 循环。"""

from types import SimpleNamespace


def make_tool_call(call_id: str, name: str, arguments: str):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def make_response(content=None, tool_calls=None):
    """非流式响应对象。"""
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self.script:
            raise AssertionError("伪造脚本已耗尽：模型被调用的次数超出预期")
        return self.script.pop(0)


class FakeClient:
    """冒充 openai.OpenAI：client.chat.completions.create(...)。"""

    def __init__(self, script):
        self.completions = FakeCompletions(script)
        self.chat = SimpleNamespace(completions=self.completions)

    @property
    def calls(self):
        return self.completions.calls


# ------------------------- 流式 chunk 工厂 -------------------------
def make_delta(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def make_stream_chunk(delta):
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def tool_delta(index, call_id=None, name=None, arguments=None):
    return SimpleNamespace(
        index=index,
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )
