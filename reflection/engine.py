"""复盘引擎：三轮对话。"""
import json
from .database import get_db, SessionModel, InsightModel, PatternModel
from .llm_client import chat
from .config import load_config


# ── 系统提示词 ─────────────────────────────

SYSTEM_PROMPT = """你是一位深具智慧的内观引导者。你的名字是「反观」。

你的角色不是导师、不是顾问、不是心理医生。你是一面镜子。

核心原则：
- 不评判、不建议、不分析、不贴标签
- 你的每个回应不超过三句话
- 保持安静、温暖、克制的语调
- 像深夜独自坐在高处看城市天际线——安静、开阔、俯瞰

第一轮（倾倒）：
- 用户倾诉，你只是接住。不追问、不引导。
- 等用户停下来，用一句话回响你听到的核心："我听到，你觉得……对吗？"

第二轮（觉察）：
- 从三个维度轻轻问一个问题，每次只问一个：
  念头层——"那时候，你心里冒出的第一句话是什么？"
  状态层——"身体有什么感觉？能量是往上的还是往下的？"
  道的层——"如果这件事是一个隐喻，它想告诉你什么？"
- 用户回答后再问另一个维度，直到三个维度都覆盖。
- 不要三个维度一起问。

第三轮（沉淀）：
- 提炼 3-5 条洞察，每条标注维度（念头 / 内在状态 / 道的体悟）。
  格式：
  [维度] 洞察内容
- 最后问："今天最值得带走的一句话是什么？"

始终用中文回应。"""


# ── 对话管理 ─────────────────────────────

def start_session(tag: str | None = None) -> tuple[int, str]:
    """创建新 session，返回 (session_id, AI 开场白)。"""
    db = get_db()
    session = SessionModel(tag=tag)
    db.add(session)
    db.commit()
    session_id = session.id

    opening = "今天，什么在你心里？"
    session.raw_conversation = json.dumps(
        [{"role": "assistant", "content": opening}], ensure_ascii=False
    )
    db.commit()
    db.close()
    return session_id, opening


def send_message(session_id: int, user_message: str) -> str:
    """在现有 session 中发送用户消息，返回 AI 回复。自动推进三轮。"""
    cfg = load_config()
    if not cfg.api_key:
        return ("还没有设置 API Key。\n\n"
                "点右上角那扇小门，在设置里填入你的 DeepSeek API Key，"
                "然后回来，我就会接住你。")

    db = get_db()
    session = db.query(SessionModel).filter_by(id=session_id).first()
    if not session:
        db.close()
        return "会话不存在。"

    history = json.loads(session.raw_conversation) if session.raw_conversation else []
    history.append({"role": "user", "content": user_message})

    user_msg_count = sum(1 for m in history if m["role"] == "user")

    prompt = _get_phase_prompt(user_msg_count)

    reply = chat(prompt, user_message, _history_for_llm(history))

    history.append({"role": "assistant", "content": reply})
    session.raw_conversation = json.dumps(history, ensure_ascii=False)

    if session.status == "active" and _has_insight_tags(reply):
        _extract_insights(db, session, history)
        session.status = "awaiting_takeaway"
    elif session.status == "awaiting_takeaway":
        session.takeaway = user_message
        session.status = "completed"

    db.commit()
    db.close()
    return reply


def _get_phase_prompt(user_msg_count: int) -> str:
    if user_msg_count <= 2:
        return SYSTEM_PROMPT + "\n当前处于第一轮（倾倒）。用户正在倾诉。不要追问，不要建议。当用户停顿下来不再继续时，用简短的一句话回响你听到的核心。"
    elif user_msg_count <= 4:
        return SYSTEM_PROMPT + "\n当前处于第二轮（觉察）。从念头/身体状态/隐喻三个维度之一轻问一个问题。每次只问一个，等用户回答后再问下一个。"
    else:
        return SYSTEM_PROMPT + "\n当前处于第三轮（沉淀）。提炼3-5条洞察，标注维度。然后问用户：今天最值得带走的一句话是什么？"


def _has_insight_tags(text: str) -> bool:
    for tag in ["[念头]", "[内在状态]", "[道的体悟]", "[念头层]", "[状态层]", "[道"]:
        if tag in text:
            return True
    return False


def _history_for_llm(history: list[dict]) -> list[dict]:
    return history[-20:] if len(history) > 20 else history


def _extract_insights(db, session: SessionModel, history: list[dict]) -> None:
    # 提取 AI 最后的洞察消息
    for m in reversed(history):
        if m["role"] == "assistant":
            last_ai_msg = m["content"]
            break
    else:
        return

    insights = []
    for dim in ["念头", "内在状态", "道的体悟"]:
        prefix = f"[{dim}]"
        if prefix in last_ai_msg:
            idx = last_ai_msg.index(prefix)
            rest = last_ai_msg[idx + len(prefix):]
            end = rest.find("[")
            text = rest[:end].strip() if end > 0 else rest.strip()
            if text:
                insights.append((_dimension_key(dim), text))

    for dim_key, text in insights:
        db.add(InsightModel(session_id=session.id, dimension=dim_key, content=text))


def _dimension_key(dim: str) -> str:
    if "念头" in dim:
        return "thought"
    if "状态" in dim or "内在" in dim:
        return "state"
    if "道" in dim:
        return "dao"
    return "thought"


# ── 历史与模式查询 ─────────────────────────

def get_sessions() -> list[dict]:
    """获取所有已完成 session 的摘要列表。"""
    db = get_db()
    sessions = (
        db.query(SessionModel)
        .filter_by(status="completed")
        .order_by(SessionModel.created_at.desc())
        .all()
    )
    result = []
    for s in sessions:
        result.append({
            "id": s.id,
            "created_at": s.created_at.isoformat(),
            "tag": s.tag,
            "takeaway": s.takeaway,
            "insight_count": len(s.insights),
        })
    db.close()
    return result


def get_session_detail(session_id: int) -> dict | None:
    """获取单个 session 的完整对话和洞察。"""
    db = get_db()
    s = db.query(SessionModel).filter_by(id=session_id).first()
    if not s:
        db.close()
        return None
    result = {
        "id": s.id,
        "created_at": s.created_at.isoformat(),
        "tag": s.tag,
        "status": s.status,
        "conversation": json.loads(s.raw_conversation) if s.raw_conversation else [],
        "insights": [
            {"dimension": i.dimension, "content": i.content}
            for i in s.insights
        ],
        "takeaway": s.takeaway,
    }
    db.close()
    return result


def get_patterns() -> list[dict]:
    """获取所有发现的长期模式。"""
    db = get_db()
    patterns = db.query(PatternModel).order_by(PatternModel.last_seen.desc()).all()
    result = [
        {
            "id": p.id,
            "type": p.ptype,
            "description": p.description,
            "first_seen": p.first_seen.isoformat(),
            "last_seen": p.last_seen.isoformat(),
            "trend": p.trend,
        }
        for p in patterns
    ]
    db.close()
    return result
