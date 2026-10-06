"""AI 业务编排层：串起「会话记忆 → Agent 推理 → 落库」。

- 非流式：chat()
- 流式：chat_stream() 产出 SSE 事件
"""

from typing import Iterator

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.logger import get_logger
from app.config import setting
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse
from app.services import chat as chat_service
from app.services.agent import runner

log = get_logger(__name__)


def _prepare(db: Session, user: User, data: ChatRequest):
    """整理出 (会话, 历史上下文, 本轮提问)。"""
    messages = data.messages or []

    def last_user_text() -> str:
        return next(
            (m.content for m in reversed(messages) if m.role == "user" and m.content.strip()),
            "",
        )

    if data.conversation_id:
        conv = chat_service.get_conversation(db, user.id, data.conversation_id)
        history = chat_service.get_history(
            db, user.id, conv.id, setting.AGENT_HISTORY_LIMIT
        )
        question = (data.content or "").strip() or last_user_text()
        return conv, history, question

    # 新会话
    question = (data.content or "").strip() or last_user_text()
    conv = chat_service.create_conversation(db, user.id, title=question or "新对话")

    history: list[dict] = []
    if messages:
        # 兼容旧前端：一次性提交的全量历史，去掉最后一条（即本轮提问）
        ms = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant") and m.content and m.content.strip()
        ]
        if ms and question and ms[-1]["content"].strip() == question:
            ms = ms[:-1]
        history = ms[-setting.AGENT_HISTORY_LIMIT :]
    return conv, history, question


def chat(db: Session, user: User, data: ChatRequest) -> ChatResponse:
    """非流式对话。"""
    conv, history, question = _prepare(db, user, data)
    if not question:
        raise BusinessException(message="请输入您要对话的内容")

    chat_service.append_message(db, conv.id, "user", question)

    result = runner.run_agent(db, user, history + [{"role": "user", "content": question}])
    content = result["content"]
    tool_calls = result["tool_calls"]

    chat_service.append_message(db, conv.id, "assistant", content, tool_calls=tool_calls)

    return ChatResponse(conversation_id=conv.id, content=content, tool_calls=tool_calls)


def chat_stream(db: Session, user: User, data: ChatRequest) -> Iterator[dict]:
    """流式对话：逐事件产出，最后一个 done 事件前完成落库。"""
    conv, history, question = _prepare(db, user, data)
    if not question:
        yield {"type": "error", "message": "请输入您要对话的内容"}
        return

    yield {"type": "meta", "conversation_id": conv.id}
    chat_service.append_message(db, conv.id, "user", question)

    full_text = ""
    trace: list[dict] = []
    try:
        for event in runner.stream_agent(
            db, user, history + [{"role": "user", "content": question}]
        ):
            if event["type"] == "done":
                full_text = event.get("content", "")
                trace = event.get("tool_calls", [])
            elif event["type"] == "error":
                full_text = event.get("message", "模型调用失败")
                yield event
                break
            yield event
    finally:
        # 无论成功与否都把已生成的内容落库，避免刷新后记录丢失
        if full_text:
            chat_service.append_message(
                db, conv.id, "assistant", full_text, tool_calls=trace
            )
        db.commit()
