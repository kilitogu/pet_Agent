from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Conversation(Base):
    """AI 会话：一次连续的多轮对话。"""

    __tablename__ = "conversations"
    __table_args__ = {"comment": "AI 会话表"}

    user_id: Mapped[int] = mapped_column(Integer, index=True, comment="所属用户ID")
    title: Mapped[str] = mapped_column(
        String(100), default="新对话", comment="会话标题（取首条提问前 20 字）"
    )


class Message(Base):
    """会话中的单条消息。role: user / assistant / tool。"""

    __tablename__ = "messages"
    __table_args__ = {"comment": "AI 消息表"}

    conversation_id: Mapped[int] = mapped_column(
        Integer, index=True, comment="所属会话ID"
    )
    role: Mapped[str] = mapped_column(String(20), comment="角色：user/assistant/tool")
    content: Mapped[str | None] = mapped_column(Text, comment="消息内容")
    tool_calls: Mapped[str | None] = mapped_column(
        Text, comment="本轮工具调用轨迹（JSON 字符串，便于回放/排查）"
    )
