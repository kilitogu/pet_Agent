"""知识库检索（RAG）。

相对初版的四点改造：
1. 懒加载 Embedding 模型（原来在模块 import 时就实例化，导入即下载模型）
2. 余弦空间（hnsw:space=cosine），让 distance 可直接还原成 0~1 相似度
3. 分块索引（见 rag/chunking.py），文档变更自动重建
4. 轻量重排：向量分 0.75 + 关键词命中率 0.25，并返回来源/章节用于引用溯源
"""

import hashlib
import json
import re

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from app.common.logger import get_logger
from app.config import BASE_DIR, setting
from app.services.rag.chunking import split_markdown

log = get_logger(__name__)

KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
COLLECTION_NAME = "pet_kb_chunks"
_INDEX_STATE = CHROMA_DIR / "kb_index_state.json"

# bge 系列推荐的非对称用法：只给 query 加指令前缀，文档侧不加
_BGE_QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

_embedding_fn = None
_client = None
_collection: Collection | None = None


def _get_embedding_fn():
    global _embedding_fn
    if _embedding_fn is None:
        log.info("加载 Embedding 模型：%s", setting.EMBEDDING_MODEL)
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=setting.EMBEDDING_MODEL
        )
    return _embedding_fn


def _fingerprint(files: list) -> str:
    h = hashlib.md5()
    for p in files:
        st = p.stat()
        h.update(f"{p.name}:{st.st_size}:{int(st.st_mtime)}".encode())
    return h.hexdigest()


def _read_text(path) -> str:
    """中文文档编码兜底：utf-8-sig → utf-8 → gb18030。"""
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="ignore")


def _new_collection() -> Collection:
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def get_collection() -> Collection:
    """向量库初始化 + 文档变更自动重建索引。"""
    global _client, _collection
    if _collection is not None:
        return _collection

    KB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    _client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    files = sorted(KB_DIR.glob("*.md"))
    fp = _fingerprint(files)

    col = _new_collection()
    old_fp = None
    if _INDEX_STATE.exists():
        try:
            old_fp = json.loads(_INDEX_STATE.read_text(encoding="utf-8")).get("fingerprint")
        except Exception:  # 状态文件损坏 → 当作失效处理
            old_fp = None

    if col.count() == 0 or old_fp != fp:
        log.info("重建知识库索引：文件数=%d", len(files))
        try:
            _client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        col = _new_collection()
        ids, docs, metas = [], [], []
        for path in files:
            text = _read_text(path).strip()
            if not text:
                continue
            for ck in split_markdown(text, source=path.name):
                ids.append(ck.id)
                docs.append(ck.text)
                metas.append(ck.metadata)
        if docs:
            # 分批写入，避免一次性过大请求
            batch = 64
            for i in range(0, len(docs), batch):
                col.add(
                    ids=ids[i : i + batch],
                    documents=docs[i : i + batch],
                    metadatas=metas[i : i + batch],
                )
        _INDEX_STATE.write_text(
            json.dumps({"fingerprint": fp, "count": len(docs)}, ensure_ascii=False),
            encoding="utf-8",
        )

    _collection = col
    return col


def _keyword_score(query: str, text: str) -> float:
    """关键词命中率：中文按标点/空格切词，命中比例越高越相关。"""
    terms = {t for t in re.split(r"[\s，。！？；、：,.!?;:]+", query) if t}
    if not terms:
        return 0.0
    return sum(1 for t in terms if t in text) / len(terms)


def search(query: str, top_k: int | None = None, min_score: float | None = None) -> list[dict]:
    """检索并重排，返回 [{score, source, section, content}]。"""
    query = (query or "").strip()
    if not query:
        return []

    top_k = top_k or setting.RAG_TOP_K
    min_score = setting.RAG_MIN_SCORE if min_score is None else min_score

    col = get_collection()
    total = col.count()
    if total == 0:
        return []

    # 先多召回再重排
    fetch = min(max(top_k * 4, 8), total)
    q = f"{_BGE_QUERY_PREFIX}{query}" if "bge" in setting.EMBEDDING_MODEL.lower() else query

    res = col.query(query_texts=[q], n_results=fetch)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    items = []
    for doc, meta, dist in zip(docs, metas, dists):
        meta = meta or {}
        vec_score = 1.0 - float(dist)  # cosine 空间下 distance = 1 - cos
        kw = _keyword_score(query, doc)
        items.append(
            {
                "score": round(0.75 * vec_score + 0.25 * kw, 4),
                "vec_score": round(vec_score, 4),
                "source": meta.get("source", "未知"),
                "section": meta.get("section", ""),
                "content": doc,
            }
        )

    items.sort(key=lambda x: x["score"], reverse=True)
    kept = [i for i in items if i["score"] >= min_score][:top_k]

    # 兜底：全都低于阈值时，至少保留最相关的一条，避免"一问三不知"
    if not kept and items:
        kept = items[:1]
        log.info("检索全部低于阈值 %.2f，兜底返回 top1（score=%.3f）", min_score, kept[0]["score"])

    log.info("RAG 检索「%s」命中 %d 条，top1=%.3f", query[:20], len(kept), kept[0]["score"] if kept else 0)
    return kept


def build_context(query: str, top_k: int | None = None) -> tuple[str, list[dict]]:
    """返回 (拼好的上下文文本, 引用列表)，供 Prompt 与前端引用展示使用。"""
    hits = search(query, top_k=top_k)
    if not hits:
        return "", []
    parts = [
        f"[片段{i + 1}] 来源《{h['source']}》· {h['section']}\n{h['content']}"
        for i, h in enumerate(hits)
    ]
    return "\n\n".join(parts), hits
