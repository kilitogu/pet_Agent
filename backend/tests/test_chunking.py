from app.services.rag.chunking import split_markdown


def test_split_by_heading_keeps_section_metadata():
    text = """# 领养流程

用户提交申请后进入待审核。

## 状态说明

待审核的记录可以取消。
"""
    chunks = split_markdown(text, "规范.md")

    assert len(chunks) == 2
    assert chunks[0].metadata["section"] == "领养流程"
    assert chunks[0].metadata["source"] == "规范.md"
    assert "待审核" in chunks[0].text
    assert chunks[1].metadata["section"] == "状态说明"


def test_long_section_is_split_and_respects_max_len():
    sentence = "这是一句用于测试长度切分的中文句子。"
    text = "# 长文档\n\n" + sentence * 60
    max_len = 200

    chunks = split_markdown(text, "long.md", max_len=max_len, overlap=20)

    assert len(chunks) > 1
    assert all(len(c.text) <= max_len for c in chunks)
    # 所有片段都应保留来源与章节，供引用溯源使用
    assert all(c.metadata["source"] == "long.md" for c in chunks)
    assert all(c.metadata["section"] == "长文档" for c in chunks)


def test_empty_text_returns_no_chunks():
    assert split_markdown("   \n\n  ", "empty.md") == []


def test_chunk_ids_are_unique():
    text = "# A\n\n" + "内容。" * 200
    chunks = split_markdown(text, "a.md", max_len=100, overlap=10)
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))
