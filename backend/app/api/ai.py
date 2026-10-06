import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import SessionLocal, get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import (
    ChatRequest,
    ConversationResponse,
    MessageResponse,
    ToolCallRecord,
)
from app.services import ai
from app.services import chat as chat_service

router = APIRouter(prefix="/ai", tags=["AI 智能助手"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # 关闭 Nginx 缓冲，保证逐字下发
}


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/chat")
def chat(data: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """非流式对话（保留兼容，便于测试与脚本调用）。"""
    return Response.success(data=ai.chat(db, current_user, data))


@router.post("/chat/stream")
def chat_stream(data: ChatRequest, current_user: User = Depends(get_current_user)):
    """流式对话（SSE）。

    注意：这里不通过 Depends(get_db) 注入会话 —— StreamingResponse 的生成器
    在请求处理函数返回之后才被消费，依赖注入的 session 可能已被关闭。
    因此在生成器内部自建 session 并负责关闭。
    """

    def event_gen():
        db = SessionLocal()
        try:
            for event in ai.chat_stream(db, current_user, data):
                yield _sse(event)
        except Exception as e:  # noqa: BLE001
            yield _sse({"type": "error", "message": f"服务异常：{type(e).__name__}"})
        finally:
            db.close()

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.get("/conversations")
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    rows = chat_service.list_conversations(db, current_user.id, limit=limit)
    return Response.success(
        data=[ConversationResponse.model_validate(r) for r in rows]
    )


@router.get("/conversations/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = chat_service.get_messages(db, current_user.id, conversation_id)

    def _parse(raw: str | None) -> list[ToolCallRecord]:
        if not raw:
            return []
        try:
            return [ToolCallRecord(**item) for item in json.loads(raw)]
        except Exception:  # noqa: BLE001
            return []

    return Response.success(
        data=[
            MessageResponse(id=r.id, role=r.role, content=r.content, tool_calls=_parse(r.tool_calls))
            for r in rows
        ]
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chat_service.delete_conversation(db, current_user.id, conversation_id)
    return Response.success(message="会话已删除")
