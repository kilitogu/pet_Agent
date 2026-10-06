from app.services.agent import tools


def test_execute_tool_rejects_unknown_tool(db, user):
    result = tools.execute_tool(db, user, "delete_everything", {})
    assert "不存在" in result


def test_execute_tool_handles_malformed_json(db, user):
    result = tools.execute_tool(db, user, "search_pets", "{不是合法json")
    assert "JSON" in result


def test_execute_tool_survives_wrong_argument_type(db, user):
    # limit 传了非数字：应当被兜底为默认值，而不是抛异常
    result = tools.execute_tool(db, user, "search_pets", '{"limit": "很多"}')
    assert "宠物" in result or "没有找到" in result


def test_search_pets_filters_by_species(db, user, pets):
    result = tools.execute_tool(db, user, "search_pets", {"species": "猫"})
    assert "咪咪" in result
    assert "雪球" in result
    assert "旺财" not in result


def test_search_pets_filters_by_status(db, user, pets):
    result = tools.execute_tool(db, user, "search_pets", {"status": 1})
    assert "咪咪" in result
    assert "旺财" in result
    assert "雪球" not in result


def test_search_pets_no_match(db, user, pets):
    result = tools.execute_tool(db, user, "search_pets", {"keyword": "不存在的小动物"})
    assert "没有找到" in result


def test_get_pet_detail_missing(db, user, pets):
    assert "不存在" in tools.execute_tool(db, user, "get_pet_detail", {"pet_id": 9999})


def test_get_pet_detail_ok(db, user, pets):
    pet_id = pets[0].id
    result = tools.execute_tool(db, user, "get_pet_detail", {"pet_id": pet_id})
    assert "咪咪" in result
    assert "待领养" in result


def test_get_my_profile(db, user):
    assert "tester" in tools.execute_tool(db, user, "get_my_profile", {})


def test_knowledge_base_tool_uses_rag(db, user, monkeypatch):
    monkeypatch.setattr(
        tools.kb,
        "build_context",
        lambda q, top_k=None: (
            "context",
            [{"source": "规范.md", "section": "领养流程", "content": "提交后待审核", "score": 0.8}],
        ),
    )
    result = tools.execute_tool(db, user, "search_knowledge_base", {"query": "怎么领养"})
    assert "规范.md" in result
    assert "领养流程" in result


def test_knowledge_base_tool_when_nothing_found(db, user, monkeypatch):
    monkeypatch.setattr(tools.kb, "build_context", lambda q, top_k=None: ("", []))
    result = tools.execute_tool(db, user, "search_knowledge_base", {"query": "无关问题"})
    assert "没有检索到" in result
