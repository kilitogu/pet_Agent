from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessage(BaseModel):
    """单条对话消息（请求 / 响应通用）。"""

    role: str
    content: str


class ChatRequest(BaseModel):
    """发起一轮对话。

    新前端只需传 content + 可选 conversation_id（服务端负责记忆）；
    messages 字段保留用于兼容旧前端的一次性全量历史提交。
    """

    content: str | None = None
    conversation_id: int | None = None
    messages: list[ChatMessage] | None = None


# 兼容旧命名（原拼写错误，保留别名不破坏已有引用）
ChatResquest = ChatRequest


class ToolCallRecord(BaseModel):
    name: str
    arguments: dict | list | str | None = None
    result: str | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    content: str
    tool_calls: list[ToolCallRecord] = []


class ConversationResponse(BaseModel):
    id: int
    title: str
    create_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str | None = None
    tool_calls: list[ToolCallRecord] = []

    model_config = ConfigDict(from_attributes=True)
