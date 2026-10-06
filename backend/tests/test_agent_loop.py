"""ReAct 循环的离线验证：用伪造客户端驱动多步工具调用与流式输出。"""

from app.services.agent import runner
from tests.fakes import (
    FakeClient,
    make_delta,
    make_response,
    make_stream_chunk,
    make_tool_call,
    tool_delta,
)


def _patch(monkeypatch, client):
    monkeypatch.setattr(runner, "_client", lambda: client)


# --------------------------------------------------------------------------
# 非流式
# --------------------------------------------------------------------------
def test_run_agent_answers_directly_without_tools(db, user, monkeypatch):
    client = FakeClient([make_response(content="你好，我是咪咪。")])
    _patch(monkeypatch, client)

    result = runner.run_agent(db, user, [{"role": "user", "content": "你是谁"}])

    assert result["content"] == "你好，我是咪咪。"
    assert result["tool_calls"] == []


def test_run_agent_calls_tool_then_answers(db, user, pets, monkeypatch):
    client = FakeClient(
        [
            make_response(tool_calls=[make_tool_call("c1", "search_pets", '{"species": "猫"}')]),
            make_response(content="目前有 2 只猫：咪咪、雪球。"),
        ]
    )
    _patch(monkeypatch, client)

    result = runner.run_agent(db, user, [{"role": "user", "content": "有哪些猫"}])

    assert result["content"] == "目前有 2 只猫：咪咪、雪球。"
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["name"] == "search_pets"
    assert "咪咪" in result["tool_calls"][0]["result"]

    # 第二次调用时，上下文里必须带上工具返回值，模型才能据此作答
    second_call_messages = client.calls[1]["messages"]
    tool_msgs = [m for m in second_call_messages if m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["tool_call_id"] == "c1"
    assert "咪咪" in tool_msgs[0]["content"]
    assert client.calls[1]["tools"] == runner.TOOL_SPECS


def test_run_agent_respects_max_steps(db, user, pets, monkeypatch):
    # 模型一直要求调工具，最多只允许 1 步
    client = FakeClient(
        [make_response(tool_calls=[make_tool_call("c1", "search_pets", "{}")])]
    )
    _patch(monkeypatch, client)

    result = runner.run_agent(db, user, [{"role": "user", "content": "查宠物"}], max_steps=1)

    assert result["content"] == runner.MAX_STEPS_FALLBACK
    assert len(client.calls) == 1


def test_run_agent_tolerates_tool_error(db, user, monkeypatch):
    # 工具名不存在 → 不应抛异常，而是把错误作为 observation 回灌
    client = FakeClient(
        [
            make_response(tool_calls=[make_tool_call("c1", "no_such_tool", "{}")]),
            make_response(content="抱歉，我查不到。"),
        ]
    )
    _patch(monkeypatch, client)

    result = runner.run_agent(db, user, [{"role": "user", "content": "随便问"}])

    assert result["content"] == "抱歉，我查不到。"
    assert "不存在" in result["tool_calls"][0]["result"]


# --------------------------------------------------------------------------
# 流式
# --------------------------------------------------------------------------
def test_stream_agent_emits_tool_events_then_deltas(db, user, pets, monkeypatch):
    script = [
        # 第 1 轮：工具调用参数分两片下发
        [
            make_stream_chunk(
                make_delta(tool_calls=[tool_delta(0, "c1", "search_pets", '{"species":')])
            ),
            make_stream_chunk(make_delta(tool_calls=[tool_delta(0, arguments='"猫"}')])),
        ],
        # 第 2 轮：逐字输出最终答案，无工具
        [
            make_stream_chunk(make_delta(content="目前有 ")),
            make_stream_chunk(make_delta(content="2 只猫。")),
        ],
    ]
    _patch(monkeypatch, FakeClient(script))

    events = list(runner.stream_agent(db, user, [{"role": "user", "content": "有哪些猫"}]))
    types = [e["type"] for e in events]

    assert types == ["tool_call", "tool_result", "delta", "delta", "done"]

    tool_call = events[0]
    assert tool_call["name"] == "search_pets"
    assert tool_call["arguments"] == {"species": "猫"}  # 分片参数被正确拼接与解析

    assert "咪咪" in events[1]["result"]

    text = "".join(e["content"] for e in events if e["type"] == "delta")
    assert text == "目前有 2 只猫。"
    assert events[-1]["content"] == "目前有 2 只猫。"
    assert events[-1]["tool_calls"][0]["name"] == "search_pets"


def test_stream_agent_plain_answer(db, user, monkeypatch):
    script = [[make_stream_chunk(make_delta(content="你好呀"))]]
    _patch(monkeypatch, FakeClient(script))

    events = list(runner.stream_agent(db, user, [{"role": "user", "content": "hi"}]))
    assert [e["type"] for e in events] == ["delta", "done"]


def test_stream_agent_reports_error_instead_of_raising(db, user, monkeypatch):
    class Boom:
        def __init__(self):
            self.chat = self

        @property
        def completions(self):
            return self

        def create(self, **kwargs):
            raise RuntimeError("网络断了")

    _patch(monkeypatch, Boom())

    events = list(runner.stream_agent(db, user, [{"role": "user", "content": "hi"}]))
    assert events[-1]["type"] == "error"
    assert "RuntimeError" in events[-1]["message"]
