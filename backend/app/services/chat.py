"""会话与消息的持久化（数据层）。

初版的对话历史完全存在前端 localStorage，刷新即丢、无法多设备、也无法审计。
这里落库后，服务端才真正"记得住"上下文。
"""

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.conversation import Conversation, Message

MAX_TITLE_LEN = 20


def auto_title(question: str) -> str:
    q = (question or "").strip().replace("\n", " ")
    return (q[:MAX_TITLE_LEN] + "…") if len(q) > MAX_TITLE_LEN else (q or "新对话")


def create_conversation(db: Session, user_id: int, title: str = "新对话") -> Conversation:
    conv = Conversation(user_id=user_id, title=auto_title(title))
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db: Session, user_id: int, conversation_id: int) -> Conversation:
    """带越权校验：只能访问自己的会话。"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise BusinessException(message="会话不存在")
    if conv.user_id != user_id:
        raise BusinessException(message="无权访问该会话", code=403)
    return conv


def list_conversations(db: Session, user_id: int, limit: int = 50) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.id.desc())
        .limit(limit)
        .all()
    )


def delete_conversation(db: Session, user_id: int, conversation_id: int) -> None:
    conv = get_conversation(db, user_id, conversation_id)
    db.query(Message).filter(Message.conversation_id == conv.id).delete()
    db.delete(conv)
    db.commit()


def append_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str | None,
    tool_calls: list | None = None,
) -> Message:
    import json

    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tool_calls=json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_history(
    db: Session, user_id: int, conversation_id: int, limit: int = 12
) -> list[dict]:
    """取最近 limit 条「可对话」消息，按时间正序返回 [{role, content}]。"""
    get_conversation(db, user_id, conversation_id)  # 越权校验
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .filter(Message.role.in_(("user", "assistant")))
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    history = [
        {"role": r.role, "content": r.content}
        for r in reversed(rows)
        if (r.content or "").strip()
    ]
    return history


def get_messages(db: Session, user_id: int, conversation_id: int) -> list[Message]:
    get_conversation(db, user_id, conversation_id)
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .filter(Message.role.in_(("user", "assistant")))
        .filter(Message.content.isnot(None))
        .order_by(Message.id.asc())
        .all()
    )
