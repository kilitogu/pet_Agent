"""会话记忆（落库）的验证。"""

import pytest

from app.common.exceptions import BusinessException
from app.services import chat as chat_service


def test_auto_title_truncates_and_handles_empty():
    assert chat_service.auto_title("怎么领养宠物") == "怎么领养宠物"
    assert chat_service.auto_title("") == "新对话"
    long_q = "一二三四五六七八九十一二三四五六七八九十一二三四五"
    assert chat_service.auto_title(long_q).endswith("…")
    assert len(chat_service.auto_title(long_q)) == chat_service.MAX_TITLE_LEN + 1


def test_append_and_read_history_in_order(db, user):
    conv = chat_service.create_conversation(db, user.id, "测试会话")
    chat_service.append_message(db, conv.id, "user", "第一问")
    chat_service.append_message(db, conv.id, "assistant", "第一答")

    history = chat_service.get_history(db, user.id, conv.id)

    assert history == [
        {"role": "user", "content": "第一问"},
        {"role": "assistant", "content": "第一答"},
    ]


def test_history_skips_tool_messages_and_empty_content(db, user):
    conv = chat_service.create_conversation(db, user.id)
    chat_service.append_message(db, conv.id, "user", "查一下")
    chat_service.append_message(db, conv.id, "assistant", "", tool_calls=[{"name": "search_pets"}])

    history = chat_service.get_history(db, user.id, conv.id)

    assert history == [{"role": "user", "content": "查一下"}]


def test_history_is_limited_to_recent_messages(db, user):
    conv = chat_service.create_conversation(db, user.id)
    for i in range(10):
        chat_service.append_message(db, conv.id, "user", f"问题{i}")

    history = chat_service.get_history(db, user.id, conv.id, limit=3)

    assert [h["content"] for h in history] == ["问题7", "问题8", "问题9"]


def test_cross_user_access_is_forbidden(db, user, admin):
    conv = chat_service.create_conversation(db, user.id, "私有会话")

    with pytest.raises(BusinessException) as exc:
        chat_service.get_history(db, admin.id, conv.id)
    assert exc.value.code == 403


def test_list_conversations_only_returns_own(db, user, admin):
    chat_service.create_conversation(db, user.id, "我的")
    chat_service.create_conversation(db, admin.id, "别人的")

    titles = [c.title for c in chat_service.list_conversations(db, user.id)]
    assert titles == ["我的"]


def test_delete_conversation_removes_messages(db, user):
    conv = chat_service.create_conversation(db, user.id)
    chat_service.append_message(db, conv.id, "user", "你好")

    chat_service.delete_conversation(db, user.id, conv.id)

    assert chat_service.list_conversations(db, user.id) == []
    from app.models.conversation import Message

    assert db.query(Message).filter(Message.conversation_id == conv.id).count() == 0


def test_tool_calls_are_persisted_as_json(db, user):
    import json

    conv = chat_service.create_conversation(db, user.id)
    trace = [{"name": "search_pets", "arguments": {"species": "猫"}, "result": "咪咪"}]
    msg = chat_service.append_message(db, conv.id, "assistant", "答案", tool_calls=trace)

    assert json.loads(msg.tool_calls) == trace
