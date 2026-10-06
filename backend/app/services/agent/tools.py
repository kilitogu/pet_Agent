"""Agent 工具层（Function Calling）。

每个工具 = 一段 OpenAI Function Schema + 一个真正访问业务数据的 Python 函数。
模型只负责"决定调用哪个工具、传什么参数"，数据一律由服务端查询后回灌，
从根本上杜绝模型编造宠物库存 / 领养状态。
"""

import json
from typing import Callable

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.logger import get_logger
from app.models.pet import Pet
from app.models.user import User
from app.services import dashboard as dashboard_service
from app.services import kb

log = get_logger(__name__)

MAX_PET_LIMIT = 10

_STATUS_LABEL = {1: "待领养", 0: "已领养"}


# --------------------------------------------------------------------------
# Function Schema：告诉模型"有哪些工具可用、参数怎么填"
# --------------------------------------------------------------------------
TOOL_SPECS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_pets",
            "description": "按关键词、物种、领养状态检索宠物库，返回宠物列表。"
            "当用户问「有哪些宠物」「帮我找一只猫/狗」「还有多少待领养的」时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "宠物名字或品种关键词，如「咪咪」「橘猫」"},
                    "species": {"type": "string", "description": "物种，只能是 猫 / 狗 / 兔 之一"},
                    "status": {
                        "type": "integer",
                        "description": "领养状态：1=待领养，0=已领养；不传表示不限",
                    },
                    "limit": {"type": "integer", "description": "返回条数，默认 5，最大 10"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pet_detail",
            "description": "根据宠物 ID 查询某只宠物的完整档案（年龄、性别、毛色、健康状况、简介、领养状态）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "pet_id": {"type": "integer", "description": "宠物 ID，来自 search_pets 的结果"}
                },
                "required": ["pet_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_stats",
            "description": "获取系统整体统计：宠物总数、待领养数、已领养数、用户数、物种分布。"
            "当用户问「一共有多少宠物」「统计一下」时使用。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "检索平台规则知识库，包含领养/预约流程、审核状态说明、宠物信息管理规则、注意事项。"
            "当用户问「怎么领养」「流程是什么」「审核要多久」「能不能取消」时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词或问题原文"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_profile",
            "description": "查询当前登录用户自己的账号信息（昵称、角色、邮箱、手机号）。",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


# --------------------------------------------------------------------------
# 工具实现
# --------------------------------------------------------------------------
def _fmt_pet(p: Pet) -> str:
    return (
        f"[{p.id}] {p.name}｜{p.species or '未知物种'}"
        f"｜{p.breed or '混血'}"
        f"｜{p.age}个月"
        f"｜{p.gender or '未知'}"
        f"｜{_STATUS_LABEL.get(p.status, '未知状态')}"
    )


def tool_search_pets(
    db: Session, user: User, keyword=None, species=None, status=None, limit=5
) -> str:
    try:
        limit = max(1, min(int(limit or 5), MAX_PET_LIMIT))
    except (TypeError, ValueError):
        limit = 5

    q = db.query(Pet)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            or_(Pet.name.ilike(like), Pet.breed.ilike(like), Pet.description.ilike(like))
        )
    if species:
        q = q.filter(Pet.species == species)
    if status is not None:
        try:
            q = q.filter(Pet.status == int(status))
        except (TypeError, ValueError):
            pass

    items = q.order_by(Pet.id.desc()).limit(limit).all()
    if not items:
        return "查询结果：没有找到符合条件的宠物。可以建议用户放宽条件，或去「宠物列表」页面查看。"

    header = f"查询到 {len(items)} 只宠物（共匹配 {q.count()} 只，仅展示前 {len(items)} 只）："
    return header + "\n" + "\n".join(_fmt_pet(p) for p in items)


def tool_get_pet_detail(db: Session, user: User, pet_id=None) -> str:
    try:
        pet_id = int(pet_id)
    except (TypeError, ValueError):
        return "错误：pet_id 必须是整数。"
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        return f"查询结果：ID={pet_id} 的宠物不存在。"
    return (
        f"【{pet.name}】档案\n"
        f"物种：{pet.species or '未知'}｜品种：{pet.breed or '未知'}｜年龄：{pet.age} 个月\n"
        f"性别：{pet.gender or '未知'}｜毛色：{pet.color or '未知'}\n"
        f"健康状况：{pet.health or '未知'}\n"
        f"领养状态：{_STATUS_LABEL.get(pet.status, '未知')}\n"
        f"简介：{pet.description or '暂无'}"
    )


def tool_get_system_stats(db: Session, user: User) -> str:
    s = dashboard_service.get_dashboard_stats(db)
    dist = "、".join(f"{d['name']} {d['value']}只" for d in s["species_distribution"]) or "暂无"
    return (
        f"系统统计：\n"
        f"宠物总数 {s['pet_total']}（待领养 {s['pet_waiting']}、已领养 {s['pet_adopted']}）\n"
        f"注册用户数 {s['user_total']}\n"
        f"物种分布：{dist}"
    )


def tool_search_knowledge_base(db: Session, user: User, query=None) -> str:
    if not query:
        return "错误：query 不能为空。"
    context, hits = kb.build_context(str(query))
    if not hits:
        return "知识库中没有检索到相关内容。请明确告知用户你查不到，不要编造规则。"
    lines = [f"[片段{i + 1}] 来源《{h['source']}》· {h['section']}（相关度 {h['score']}）\n{h['content']}" for i, h in enumerate(hits)]
    return "\n\n".join(lines)


def tool_get_my_profile(db: Session, user: User) -> str:
    return (
        f"当前用户：{user.name}（账号 {user.username}）\n"
        f"角色：{'管理员' if user.role == 'admin' else '普通用户'}\n"
        f"邮箱：{user.email or '未填写'}｜手机号：{user.phone or '未填写'}"
    )


# --------------------------------------------------------------------------
# 注册表：白名单机制，模型只能调用这里登记过的工具
# --------------------------------------------------------------------------
TOOL_REGISTRY: dict[str, Callable[..., str]] = {
    "search_pets": tool_search_pets,
    "get_pet_detail": tool_get_pet_detail,
    "get_system_stats": tool_get_system_stats,
    "search_knowledge_base": tool_search_knowledge_base,
    "get_my_profile": tool_get_my_profile,
}


def execute_tool(db: Session, user: User, name: str, arguments: dict | str | None) -> str:
    """执行工具：白名单校验 + 参数解析 + 异常兜底（绝不把裸异常抛给模型）。"""
    if name not in TOOL_REGISTRY:
        log.warning("模型试图调用未注册的工具：%s", name)
        return f"错误：工具 {name} 不存在。"

    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments) if arguments.strip() else {}
        except json.JSONDecodeError:
            return "错误：工具参数不是合法 JSON。"
    arguments = arguments or {}

    try:
        return TOOL_REGISTRY[name](db, user, **arguments)
    except TypeError as e:
        log.warning("工具 %s 参数错误：%s", name, e)
        return f"错误：工具 {name} 的参数不合法（{e}）。"
    except Exception as e:  # noqa: BLE001  工具失败不应中断整个 Agent 循环
        log.exception("工具 %s 执行失败", name)
        return f"错误：工具 {name} 执行失败（{type(e).__name__}）。"
