"""Markdown 分块：把一篇文档切成"语义完整 + 长度可控"的知识片段。

原实现把整个 .md 当成一个 chunk 塞进向量库（kb.py: docs.append(text)），
文档一长，检索结果就会被无关内容稀释 —— 这里按标题切章节、再按长度二次切分。
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

# 中文优先的分隔符：先段落、再句号，最后才是逗号
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？；\n])")


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


def _split_long(text: str, max_len: int, overlap: int) -> list[str]:
    """把超长段落按句子边界切成 <= max_len 的片段，带 overlap 缓解断句。"""
    sentences = [s for s in _SENTENCE_SPLIT.split(text) if s and s.strip()]
    chunks: list[str] = []
    buf = ""
    for sent in sentences:
        if len(buf) + len(sent) <= max_len:
            buf += sent
        else:
            if buf.strip():
                chunks.append(buf.strip())
            # 保留尾部 overlap 个字符，避免句子被硬切断导致语义丢失
            buf = (buf[-overlap:] if overlap and buf else "") + sent
    if buf.strip():
        chunks.append(buf.strip())
    # 兜底：极长的单句仍然超限时，直接按字符窗口硬切
    result: list[str] = []
    for c in chunks:
        if len(c) <= max_len:
            result.append(c)
        else:
            for i in range(0, len(c), max_len - overlap or max_len):
                result.append(c[i : i + max_len])
    return result


def split_markdown(
    text: str, source: str, max_len: int = 400, overlap: int = 60
) -> list[Chunk]:
    """按 Markdown 标题切章节，章节内超长再二次切分。

    metadata 会带上 source（文件名）与 section（标题），供答案引用溯源使用。
    """
    text = text.strip()
    if not text:
        return []

    # 1) 按标题收集章节
    sections: list[tuple[str, str]] = []
    current_head = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s+", line):
            if current_lines:
                sections.append((current_head, "\n".join(current_lines).strip()))
            current_head = re.sub(r"^#{1,6}\s+", "", line).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_head, "\n".join(current_lines).strip()))

    # 2) 章节内按长度切分
    chunks: list[Chunk] = []
    stem = Path(source).stem
    seq = 0
    for section, body in sections:
        if not body:
            continue
        for piece in _split_long(body, max_len, overlap):
            chunks.append(
                Chunk(
                    id=f"{stem}-{seq}",
                    text=piece,
                    metadata={
                        "source": source,
                        "section": section or "正文",
                        "chunk_index": seq,
                    },
                )
            )
            seq += 1
    return chunks
