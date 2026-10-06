"""Agent 执行器：ReAct（Reasoning + Acting）多步循环。

一次用户提问的处理流程：
    模型决策 → (可选) 调用工具 → 工具结果回灌 → 模型再决策 → ... → 输出最终答案

相比初版"检索一次直接回答"，这里的关键差异：
- 模型可以自主"多步"取数（先搜列表 → 再查详情 → 再查规则）
- 工具真正访问数据库，杜绝编造
- 带最大步数保护、白名单校验、异常兜底
"""

import json
from typing import Iterator

from openai import OpenAI
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.logger import get_logger
from app.config import setting
from app.models.user import User
from app.services.agent.tools import TOOL_SPECS, execute_tool

log = get_logger(__name__)

SYSTEM_PROMPT = """你是「咪咪」，宠物领养平台的智能助手。你可以调用工具查询真实数据来回答问题。

工作要求：
1. 涉及具体宠物、库存、领养状态、平台规则时，必须先调用工具查证，禁止凭印象编造。
2. 可以多步调用：例如先 search_pets 找到候选，再用 get_pet_detail 看详情。
3. 引用知识库规则时，标注来源，例如（来源：规范.md · 领养/预约流程）。
4. 工具查不到的内容，如实说明「没有查到」，并引导用户去对应页面查看，不要硬编。
5. 与宠物领养、养护、平台使用无关的问题，礼貌拒答并引导回主题。
6. 回答简洁、条理清晰，用中文。
"""

MAX_STEPS_FALLBACK = "抱歉，这次查询步骤太多了，我先把已知信息给你，你可以再问得具体一些。"


def _client() -> OpenAI:
    if not setting.DEEPSEEK_KEY:
        raise BusinessException(message="未获取到大模型的 API Key")
    return OpenAI(api_key=setting.DEEPSEEK_KEY, base_url=setting.DEEPSEEK_URL)


def _api_messages(history: list[dict], context: str = "") -> list[dict]:
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n【已检索到的平台资料】\n{context}"
    msgs = [{"role": "system", "content": system}]
    for m in history:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content})
    return msgs


def _assistant_tool_message(content: str | None, tool_calls: list[dict]) -> dict:
    return {
        "role": "assistant",
        "content": content or "",
        "tool_calls": [
            {
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            }
            for tc in tool_calls
        ],
    }


# ==========================================================================
# 非流式
# ==========================================================================
def run_agent(db: Session, user: User, history: list[dict], max_steps: int | None = None) -> dict:
    """跑完整个 ReAct 循环，返回 {content, tool_calls}。"""
    max_steps = max_steps or setting.AGENT_MAX_STEPS
    client = _client()
    messages = _api_messages(history)
    trace: list[dict] = []

    for step in range(max_steps):
        resp = client.chat.completions.create(
            model=setting.DEEPSEEK_MODEL,
            messages=messages,
            tools=TOOL_SPECS,
            tool_choice="auto",
            temperature=0.3,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            log.info("Agent 第 %d 步结束，输出最终答案", step + 1)
            return {"content": (msg.content or "").strip() or MAX_STEPS_FALLBACK, "tool_calls": trace}

        calls = [
            {
                "id": tc.id,
                "name": tc.function.name,
                "arguments": tc.function.arguments or "{}",
            }
            for tc in msg.tool_calls
        ]
        messages.append(_assistant_tool_message(msg.content, calls))

        for c in calls:
            log.info("Agent 调用工具：%s(%s)", c["name"], c["arguments"])
            result = execute_tool(db, user, c["name"], c["arguments"])
            trace.append({"name": c["name"], "arguments": c["arguments"], "result": result})
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})

    log.warning("Agent 达到最大步数 %d，强制收尾", max_steps)
    return {"content": MAX_STEPS_FALLBACK, "tool_calls": trace}


# ==========================================================================
# 流式（SSE）：边思考边把 token / 工具调用推给前端
# ==========================================================================
def stream_agent(
    db: Session, user: User, history: list[dict], max_steps: int | None = None
) -> Iterator[dict]:
    """逐事件产出：tool_call / tool_result / delta / done / error。"""
    max_steps = max_steps or setting.AGENT_MAX_STEPS
    client = _client()
    messages = _api_messages(history)
    trace: list[dict] = []

    try:
        for step in range(max_steps):
            stream = client.chat.completions.create(
                model=setting.DEEPSEEK_MODEL,
                messages=messages,
                tools=TOOL_SPECS,
                tool_choice="auto",
                temperature=0.3,
                stream=True,
            )

            content_parts: list[str] = []
            tool_buf: dict[int, dict] = {}

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                if delta.content:
                    content_parts.append(delta.content)
                    yield {"type": "delta", "content": delta.content}

                # 工具调用是分片传输的，按 index 累积 id / name / arguments
                for tc in delta.tool_calls or []:
                    buf = tool_buf.setdefault(
                        tc.index, {"id": "", "name": "", "arguments": ""}
                    )
                    if tc.id:
                        buf["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            buf["name"] += tc.function.name
                        if tc.function.arguments:
                            buf["arguments"] += tc.function.arguments

            # 没有工具调用 → 本轮就是最终答案
            if not tool_buf:
                yield {
                    "type": "done",
                    "content": "".join(content_parts).strip(),
                    "tool_calls": trace,
                }
                return

            calls = [
                {"id": b["id"] or f"call_{i}", "name": b["name"], "arguments": b["arguments"] or "{}"}
                for i, b in sorted(tool_buf.items())
            ]
            messages.append(_assistant_tool_message("".join(content_parts), calls))

            for c in calls:
                log.info("Agent 调用工具：%s(%s)", c["name"], c["arguments"])
                yield {"type": "tool_call", "name": c["name"], "arguments": _safe_args(c["arguments"])}

                result = execute_tool(db, user, c["name"], c["arguments"])
                trace.append({"name": c["name"], "arguments": c["arguments"], "result": result})
                yield {"type": "tool_result", "name": c["name"], "result": result}

                messages.append({"role": "tool", "tool_call_id": c["id"], "content": result})

        yield {"type": "done", "content": MAX_STEPS_FALLBACK, "tool_calls": trace}

    except BusinessException:
        raise
    except Exception as e:  # noqa: BLE001
        log.exception("Agent 流式执行失败")
        yield {"type": "error", "message": f"模型调用失败：{type(e).__name__}"}


def _safe_args(raw: str) -> dict | str:
    try:
        return json.loads(raw) if raw and raw.strip() else {}
    except json.JSONDecodeError:
        return raw
