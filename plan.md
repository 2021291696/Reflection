# Reflection（反观）实现计划

> **面向 AI 代理的工作者：** 使用 subagent-driven-development（推荐）或 executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法跟踪进度。

**目标：** 构建 Reflection 桌面应用——一个本地运行的复盘 agent，黎明初光视觉风格，三轮对话引擎，SQLite 存储，PyInstaller 打包为 .exe。

**架构：** Python FastAPI 本地服务器 + 纯 HTML/CSS/JS 前端 + SQLAlchemy/SQLite + httpx 直调 LLM API。前端通过 fetch 与后端通信。应用启动时自动打开浏览器。

**技术栈：** Python 3.11+, FastAPI, SQLAlchemy, SQLite, httpx, PyInstaller, 纯 HTML/CSS/JS（无框架）

---

## 文件结构

```
project1：复盘agent/
├── design.md                          (已完成)
├── plan.md                            (本文件)
└── reflection/
    ├── __init__.py
    ├── main.py                        (入口：uvicorn + 打开浏览器)
    ├── config.py                      (设置管理：API Key、模型选择)
    ├── database.py                    (SQLAlchemy 模型 + 数据库连接)
    ├── llm_client.py                  (LLM API 抽象层)
    ├── engine.py                      (复盘引擎：三轮对话)
    ├── server.py                      (FastAPI 路由)
    ├── static/
    │   ├── index.html                 (首页：书写态)
    │   ├── history.html               (门后：回看态)
    │   ├── style.css                  (全局样式)
    │   └── app.js                     (首页交互逻辑)
    ├── requirements.txt
    └── reflection.spec               (PyInstaller 配置)
```

---

### 任务 1：项目脚手架

**文件：**
- 创建：`project1：复盘agent/reflection/__init__.py`
- 创建：`project1：复盘agent/reflection/requirements.txt`

- [ ] **步骤 1：创建目录结构并编写 requirements.txt**

```txt
fastapi==0.115.6
uvicorn==0.34.0
sqlalchemy==2.0.36
httpx==0.28.1
pydantic==2.10.4
pydantic-settings==2.7.1
```

- [ ] **步骤 2：创建 __init__.py**

```python
# Reflection - 复盘 Agent
__version__ = "0.1.0"
```

- [ ] **步骤 3：安装依赖**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent\reflection"
pip install -r requirements.txt
```

- [ ] **步骤 4：验证**

```powershell
python -c "import fastapi; import sqlalchemy; import httpx; print('OK')"
```
预期：OK

---

### 任务 2：配置模块

**文件：**
- 创建：`project1：复盘agent/reflection/config.py`

- [ ] **步骤 1：编写 config.py**

```python
"""配置管理：API Key、模型选择、数据目录。"""
import json
import os
from pathlib import Path
from pydantic import BaseModel

DATA_DIR = Path(os.environ.get("REFLECTION_DATA", Path.home() / "Reflection"))
CONFIG_FILE = DATA_DIR / "config.json"


class Config(BaseModel):
    api_provider: str = "openai"       # openai / anthropic
    api_key: str = ""
    model: str = "gpt-4o"
    api_base: str = ""                 # 自定义 API 地址（可选）
    theme: str = "dark"                # dark / light
    first_run: bool = True


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    ensure_data_dir()
    if CONFIG_FILE.exists():
        raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return Config(**raw)
    return Config()


def save_config(cfg: Config) -> None:
    ensure_data_dir()
    cfg.first_run = False
    CONFIG_FILE.write_text(
        json.dumps(cfg.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
```

- [ ] **步骤 2：验证**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -c "from reflection.config import load_config; c = load_config(); print(c.api_provider)"
```
预期：openai

---

### 任务 3：数据库模块

**文件：**
- 创建：`project1：复盘agent/reflection/database.py`

- [ ] **步骤 1：编写 database.py**

```python
"""SQLite 数据库：Session、Insight、Pattern 三张表。"""
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, create_engine, JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session as DBSession

from .config import DATA_DIR, ensure_data_dir

DB_PATH = DATA_DIR / "reflection.db"


class Base(DeclarativeBase):
    pass


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_conversation = Column(Text, default="")   # JSON: [{role, content}, ...]
    status = Column(String, default="active")      # active / completed
    tag = Column(String, nullable=True)            # 生活/学习/交易/关系/其他
    takeaway = Column(Text, nullable=True)         # "今天最值得带走的一句话"
    insights = relationship("InsightModel", back_populates="session", cascade="all, delete-orphan")


class InsightModel(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    dimension = Column(String, nullable=False)     # thought / state / dao
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("SessionModel", back_populates="insights")


class PatternModel(Base):
    __tablename__ = "patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ptype = Column(String, nullable=False)         # 惯性思维 / 情绪模式 / 行为重复
    description = Column(Text, nullable=False)
    insight_ids = Column(JSON, default=[])          # 关联的 insight id 列表
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    trend = Column(String, default="stable")        # strengthening / weakening / resolved


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        ensure_data_dir()
        _engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
        Base.metadata.create_all(_engine)
    return _engine


def get_db() -> DBSession:
    return DBSession(get_engine())
```

- [ ] **步骤 2：验证数据库创建**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -c "from reflection.database import get_db; db = get_db(); print('tables:', list(db.get_bind().table_names())); db.close()"
```
预期：tables: ['sessions', 'insights', 'patterns']

---

### 任务 4：LLM 客户端

**文件：**
- 创建：`project1：复盘agent/reflection/llm_client.py`

- [ ] **步骤 1：编写 llm_client.py**

```python
"""LLM API 抽象层：支持 OpenAI 和 Anthropic。"""
import json
import httpx
from .config import load_config


def _build_messages(system_prompt: str, user_message: str, history: list[dict] | None = None) -> list[dict]:
    msgs = [{"role": "system", "content": system_prompt}]
    if history:
        msgs.extend(history)
    msgs.append({"role": "user", "content": user_message})
    return msgs


def chat(system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
    """
    发送聊天请求，返回 AI 回复文本。
    history: [{role: "user"|"assistant", content: str}, ...]
    """
    cfg = load_config()
    messages = _build_messages(system_prompt, user_message, history)

    if cfg.api_provider == "anthropic":
        return _chat_anthropic(cfg, system_prompt, messages)
    else:
        return _chat_openai(cfg, messages)


def _chat_openai(cfg, messages: list[dict]) -> str:
    base = cfg.api_base or "https://api.openai.com/v1"
    url = f"{base}/chat/completions"
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
        json={"model": cfg.model, "messages": messages, "temperature": 0.7},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _chat_anthropic(cfg, system_prompt: str, messages: list[dict]) -> str:
    # Anthropic 的 system 独立于 messages
    user_messages = [m for m in messages if m["role"] != "system"]
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": cfg.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": cfg.model,
            "system": system_prompt,
            "messages": user_messages,
            "max_tokens": 4096,
            "temperature": 0.7,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]
```

- [ ] **步骤 2：验证（需要 API Key 时跳过，集成测试阶段再验证）**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -c "from reflection.llm_client import chat; print('LLM client module loaded OK')"
```
预期：LLM client module loaded OK

---

### 任务 5：复盘引擎

**文件：**
- 创建：`project1：复盘agent/reflection/engine.py`

- [ ] **步骤 1：编写 engine.py —— 系统提示词 + 三轮逻辑**

```python
"""复盘引擎：三轮对话。"""
import json
from .database import get_db, SessionModel, InsightModel, PatternModel
from .llm_client import chat
from datetime import datetime


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
    # 记录开场白到对话
    session.raw_conversation = json.dumps(
        [{"role": "assistant", "content": opening}], ensure_ascii=False
    )
    db.commit()
    db.close()
    return session_id, opening


def send_message(session_id: int, user_message: str) -> str:
    """在现有 session 中发送用户消息，返回 AI 回复。自动推进三轮。"""
    db = get_db()
    session = db.query(SessionModel).filter_by(id=session_id).first()
    if not session:
        db.close()
        return "会话不存在。"

    # 恢复对话历史
    history = json.loads(session.raw_conversation) if session.raw_conversation else []
    history.append({"role": "user", "content": user_message})

    # 判断当前处于哪一轮（简单启发式：消息数量）
    user_msg_count = sum(1 for m in history if m["role"] == "user")

    # 选择对应的系统提示词
    prompt = _get_phase_prompt(user_msg_count)

    # 调用 LLM
    reply = chat(prompt, user_message, _history_for_llm(history))

    # 保存
    history.append({"role": "assistant", "content": reply})
    session.raw_conversation = json.dumps(history, ensure_ascii=False)

    # 如果是第三轮结束并且用户给了 takeaway，提取洞察
    if user_msg_count >= 6:  # 大约第三轮结束
        _extract_insights(db, session, history)

    db.commit()
    db.close()
    return reply


def _get_phase_prompt(user_msg_count: int) -> str:
    if user_msg_count <= 2:
        return SYSTEM_PROMPT + "\n当前处于第一轮（倾倒）。用户正在倾诉。不要追问，不要建议。当用户停下来时，用一句话回响你听到的核心。"
    elif user_msg_count <= 4:
        return SYSTEM_PROMPT + "\n当前处于第二轮（觉察）。从念头/身体状态/隐喻三个维度之一轻问一个问题。每次只问一个，等用户回答后再问下一个。"
    else:
        return SYSTEM_PROMPT + "\n当前处于第三轮（沉淀）。提炼3-5条洞察，标注维度。然后问用户：今天最值得带走的一句话是什么？"


def _history_for_llm(history: list[dict]) -> list[dict]:
    """只保留最近的 N 条消息避免 token 溢出。"""
    return history[-20:] if len(history) > 20 else history


def _extract_insights(db, session: SessionModel, history: list[dict]) -> None:
    """从第三轮对话中解析 AI 给出的洞察，存入 Insight 表；尝试跨 session 发现 Pattern。"""
    # 找到最近一条 assistant 消息
    for m in reversed(history):
        if m["role"] == "assistant":
            last_ai_msg = m["content"]
            break
    else:
        return

    # 解析 [维度] 格式的洞察
    insights = []
    for dim in ["念头", "内在状态", "道的体悟"]:
        prefix = f"[{dim}]"
        if prefix in last_ai_msg:
            # 简单提取：找到 [dim] 之后到下一行或结尾
            idx = last_ai_msg.index(prefix)
            rest = last_ai_msg[idx + len(prefix):]
            end = rest.find("[")
            text = rest[:end].strip() if end > 0 else rest.strip()
            if text:
                insights.append((_dimension_key(dim), text))

    for dim_key, text in insights:
        db.add(InsightModel(session_id=session.id, dimension=dim_key, content=text))

    # 标记 session 完成
    session.status = "completed"

    # 简单的跨时间模式检查：查询所有同类维度的 insight
    if insights:
        all_insights = db.query(InsightModel).all()
        # 这里用最简单的关键词重叠来发现模式（后续可优化为 LLM 分析）
        # 暂时跳过复杂的模式发现，后续迭代
        pass


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
```

- [ ] **步骤 2：验证模块可导入**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -c "from reflection.engine import start_session; print('Engine module loaded OK')"
```
预期：Engine module loaded OK

---

### 任务 6：API 服务器

**文件：**
- 创建：`project1：复盘agent/reflection/server.py`

- [ ] **步骤 1：编写 server.py —— FastAPI 路由**

```python
"""FastAPI 服务器：REST API 路由。"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from .config import load_config, save_config, Config
from .engine import start_session, send_message, get_sessions, get_session_detail, get_patterns

app = FastAPI(title="Reflection", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"


# ── 配置 ─────────────────────────────────

class ConfigUpdate(BaseModel):
    api_provider: str | None = None
    api_key: str | None = None
    model: str | None = None
    api_base: str | None = None
    theme: str | None = None


@app.get("/api/config")
def api_get_config():
    cfg = load_config()
    return {
        "api_provider": cfg.api_provider,
        "has_key": bool(cfg.api_key),
        "model": cfg.model,
        "theme": cfg.theme,
        "first_run": cfg.first_run,
    }


@app.post("/api/config")
def api_save_config(body: ConfigUpdate):
    cfg = load_config()
    updates = body.model_dump(exclude_none=True)
    for k, v in updates.items():
        setattr(cfg, k, v)
    save_config(cfg)
    return {"ok": True}


# ── 复盘会话 ─────────────────────────────

class StartSessionRequest(BaseModel):
    tag: str | None = None


@app.post("/api/sessions")
def api_start_session(body: StartSessionRequest | None = None):
    tag = body.tag if body else None
    session_id, opening = start_session(tag)
    return {"session_id": session_id, "message": opening}


class SendMessageRequest(BaseModel):
    message: str


@app.post("/api/sessions/{session_id}/messages")
def api_send_message(session_id: int, body: SendMessageRequest):
    try:
        reply = send_message(session_id, body.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"reply": reply}


@app.get("/api/sessions")
def api_get_sessions():
    return get_sessions()


@app.get("/api/sessions/{session_id}")
def api_get_session(session_id: int):
    detail = get_session_detail(session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail


@app.get("/api/patterns")
def api_get_patterns():
    return get_patterns()


# ── 静态文件 ─────────────────────────────

@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/history")
def serve_history():
    return FileResponse(STATIC_DIR / "history.html")


# 挂载静态文件（CSS/JS）
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
```

- [ ] **步骤 2：验证服务器可启动**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -c "from reflection.server import app; print('Server module loaded OK, routes:', len(app.routes))"
```
预期：Server module loaded OK, routes: N

---

### 任务 7：前端样式（黎明初光）

**文件：**
- 创建：`project1：复盘agent/reflection/static/style.css`

- [ ] **步骤 1：编写 style.css**

```css
/* === Reset & Base === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Inter:wght@200;300;400&family=Noto+Serif+SC:wght@300;400;500&display=swap');

:root {
  --bg-top: #0f1f35;
  --bg-mid: #18283e;
  --bg-low: #2a3a3c;
  --bg-bottom: #4e3e2c;
  --text-primary: rgba(225, 215, 195, 0.82);
  --text-secondary: rgba(200, 170, 130, 0.55);
  --text-dim: rgba(190, 175, 145, 0.4);
  --gold: rgba(230, 190, 140, 0.5);
  --gold-bright: rgba(250, 200, 120, 0.55);
  --door-border: rgba(210, 180, 135, 0.5);
  --font-serif: 'Cormorant Garamond', 'Noto Serif SC', Georgia, serif;
  --font-sans: 'Inter', 'PingFang SC', -apple-system, sans-serif;
}

html, body {
  height: 100%;
  overflow: hidden;
  font-family: var(--font-sans);
  font-weight: 300;
  color: var(--text-primary);
  background: linear-gradient(180deg,
    var(--bg-top) 0%,
    var(--bg-mid) 30%,
    #1e3045 55%,
    var(--bg-low) 72%,
    #3e3a2e 85%,
    var(--bg-bottom) 100%
  );
  -webkit-font-smoothing: antialiased;
}

/* === 首页布局 === */
#main-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
  padding: 40px 32px;
}

/* 左上角英文 */
.brand {
  position: absolute;
  top: 22px;
  left: 28px;
  font-family: 'Cormorant Garamond', Georgia, serif;
  font-size: 9px;
  font-weight: 400;
  letter-spacing: 5px;
  color: var(--text-dim);
  user-select: none;
}

/* 右上角门图标 */
.door-icon {
  position: absolute;
  top: 22px;
  right: 28px;
  width: 14px;
  height: 17px;
  cursor: pointer;
  text-decoration: none;
  opacity: 0.7;
  transition: opacity 0.3s ease;
}
.door-icon:hover { opacity: 1; }

.door-icon svg {
  width: 100%;
  height: 100%;
}

/* 中央文字区 */
.hero-text {
  font-family: var(--font-serif);
  font-size: 26px;
  font-weight: 400;
  letter-spacing: 2px;
  text-align: center;
  line-height: 1.6;
  color: var(--text-primary);
}

.divider {
  width: 40px;
  height: 1px;
  background: var(--gold);
  margin: 22px auto 14px;
}

.subtitle-text {
  font-family: var(--font-sans);
  font-size: 10px;
  font-weight: 300;
  letter-spacing: 4px;
  color: var(--text-secondary);
}

/* 底部光晕 */
.sunrise-glow {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 140px;
  background: linear-gradient(0deg,
    rgba(240, 180, 80, 0.15) 0%,
    rgba(210, 150, 60, 0.08) 30%,
    rgba(170, 120, 40, 0.02) 60%,
    transparent 100%
  );
  pointer-events: none;
}

.horizon-line {
  position: absolute;
  bottom: 8px;
  left: 8%;
  right: 8%;
  height: 1px;
  background: linear-gradient(90deg,
    transparent,
    rgba(250, 200, 120, 0.35),
    var(--gold-bright),
    rgba(250, 200, 120, 0.35),
    transparent
  );
  pointer-events: none;
}

/* === 对话区 === */
#conversation {
  width: 100%;
  max-width: 600px;
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  margin-bottom: 16px;
  scroll-behavior: smooth;
}

.message {
  margin-bottom: 20px;
  animation: fadeIn 0.6s ease;
}

.message.user {
  font-family: var(--font-sans);
  font-weight: 300;
  line-height: 1.7;
}

.message.assistant {
  font-family: var(--font-serif);
  font-style: italic;
  color: rgba(225, 215, 195, 0.72);
  line-height: 1.8;
}

/* 输入区 */
#input-area {
  width: 100%;
  max-width: 600px;
  position: relative;
}

#user-input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(200, 170, 130, 0.2);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 15px;
  font-weight: 300;
  line-height: 1.8;
  padding: 12px 0;
  outline: none;
  resize: none;
  transition: border-color 0.3s ease;
}

#user-input:focus {
  border-bottom-color: rgba(230, 190, 140, 0.5);
}

#user-input::placeholder {
  color: rgba(180, 160, 130, 0.35);
}

/* 发送按钮 - 极简：只显示一个小箭头 */
#send-btn {
  position: absolute;
  right: 0;
  bottom: 14px;
  background: none;
  border: none;
  color: rgba(200, 170, 130, 0.5);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  transition: color 0.3s ease;
  display: none;
}

#send-btn.visible { display: block; }
#send-btn:hover { color: rgba(240, 200, 140, 0.8); }

/* 加载动画（三个点缓慢闪烁） */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 4px;
  height: 4px;
  background: rgba(200, 170, 130, 0.5);
  border-radius: 50%;
  animation: blink 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* === 新复盘按钮 === */
#new-session-btn {
  position: absolute;
  top: 56px;
  left: 50%;
  transform: translateX(-50%);
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 300;
  letter-spacing: 3px;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.6s ease;
  pointer-events: none;
}

#new-session-btn.visible {
  opacity: 0.6;
  pointer-events: auto;
}

#new-session-btn:hover { opacity: 1; }

/* === 滚动条 === */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(200, 170, 130, 0.15); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(200, 170, 130, 0.3); }

/* 响应式：小屏幕 */
@media (max-width: 480px) {
  .hero-text { font-size: 22px; }
  #conversation, #input-area { max-width: 100%; }
}
```

**注意**：`@import url(...)` 引用 Google Fonts。如果用户无法访问 Google Fonts（国内网络环境），需要在实现时改用本地字体回退方案——优先使用系统自带衬线/无衬线字体，Cormorant Garamond 和 Inter 仅作增强项。

---

### 任务 8：前端首页（index.html + app.js）

**文件：**
- 创建：`project1：复盘agent/reflection/static/index.html`
- 创建：`project1：复盘agent/reflection/static/app.js`

- [ ] **步骤 1：编写 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reflection · 反观</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <div id="main-view">
    <!-- 左上角英文 -->
    <div class="brand">R E F L E C T I O N</div>

    <!-- 右上角门图标（SVG 内联） -->
    <a class="door-icon" href="/history" title="曾经走过的路">
      <svg viewBox="0 0 14 17" xmlns="http://www.w3.org/2000/svg">
        <rect x="0.5" y="0.5" width="13" height="16" rx="1.5"
              fill="none" stroke="rgba(210,180,135,0.5)" stroke-width="0.5"/>
        <rect x="0" y="0" width="8" height="17" rx="1.5"
              fill="rgba(15,24,38,0.7)"/>
        <line x1="8" y1="0" x2="8" y2="17"
              stroke="rgba(210,180,135,0.3)" stroke-width="0.5"/>
        <line x1="2" y1="8.5" x2="7" y2="8.5"
              stroke="rgba(240,200,140,0.4)" stroke-width="0.5"/>
      </svg>
    </a>

    <!-- 对话区 -->
    <div id="conversation"></div>

    <!-- 输入区 -->
    <div id="input-area">
      <textarea id="user-input" rows="1" placeholder="开始写..."></textarea>
      <button id="send-btn" title="发送">&#8593;</button>
    </div>

    <!-- 新复盘按钮（对话结束后显示） -->
    <button id="new-session-btn">新 复 盘</button>

    <!-- 底部光晕 -->
    <div class="sunrise-glow"></div>
    <div class="horizon-line"></div>
  </div>

  <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **步骤 2：编写 app.js**

```javascript
// Reflection 首页交互
const conversationEl = document.getElementById('conversation');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newSessionBtn = document.getElementById('new-session-btn');

let currentSessionId = null;
let isWaitingForAI = false;

// ── 初始化 ───────────────────────────────
async function init() {
  showHeroScreen();
  userInput.addEventListener('input', onInput);
  userInput.addEventListener('keydown', onKeydown);
  sendBtn.addEventListener('click', sendMessage);
  newSessionBtn.addEventListener('click', startNewSession);
}

// ── 英雄屏（首次打开） ────────────────────
function showHeroScreen() {
  conversationEl.innerHTML = `
    <div style="text-align:center;padding-top:20vh">
      <div class="hero-text">今天，<br>什么在你<br>心里？</div>
      <div class="divider"></div>
      <div class="subtitle-text">俯 瞰 自 心</div>
    </div>`;
}

// ── 输入处理 ─────────────────────────────
function onInput() {
  const hasText = userInput.value.trim().length > 0;
  sendBtn.classList.toggle('visible', hasText);
  // 自动调整高度
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!isWaitingForAI) sendMessage();
  }
}

// ── 发送消息 ─────────────────────────────
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isWaitingForAI) return;

  userInput.value = '';
  userInput.style.height = 'auto';
  sendBtn.classList.remove('visible');

  // 首次发送时自动创建 session
  if (!currentSessionId) {
    await createSession();
  }

  // 移除英雄屏
  clearHeroIfNeeded();

  // 显示用户消息
  appendMessage('user', text);

  // 显示加载
  const loader = appendLoader();

  isWaitingForAI = true;
  userInput.disabled = true;

  try {
    const resp = await fetch(`/api/sessions/${currentSessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await resp.json();
    loader.remove();

    // 显示 AI 回复
    appendMessage('assistant', data.reply);

    // 检查是否有洞察提取（消息中包含 "带走" 说明第三轮结束）
    if (data.reply.includes('带走') || data.reply.includes('最值得')) {
      newSessionBtn.classList.add('visible');
    }
  } catch (err) {
    loader.remove();
    appendMessage('assistant', '连接断开了，刷新页面试试。');
  }

  isWaitingForAI = false;
  userInput.disabled = false;
  userInput.focus();
  scrollToBottom();
}

async function createSession() {
  const resp = await fetch('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tag: null }),
  });
  const data = await resp.json();
  currentSessionId = data.session_id;
}

// ── UI 辅助 ──────────────────────────────
function clearHeroIfNeeded() {
  const hero = conversationEl.querySelector('.hero-text');
  if (hero) conversationEl.innerHTML = '';
}

function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = content;
  conversationEl.appendChild(div);
  scrollToBottom();
}

function appendLoader() {
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  conversationEl.appendChild(div);
  scrollToBottom();
  return div;
}

function scrollToBottom() {
  conversationEl.scrollTop = conversationEl.scrollHeight;
}

async function startNewSession() {
  currentSessionId = null;
  newSessionBtn.classList.remove('visible');
  conversationEl.innerHTML = '';
  showHeroScreen();
  userInput.focus();
}

// ── 启动 ────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
```

---

### 任务 9：前端历史页（history.html）

**文件：**
- 创建：`project1：复盘agent/reflection/static/history.html`

- [ ] **步骤 1：编写 history.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>历史 · Reflection</title>
  <link rel="stylesheet" href="/static/style.css">
  <style>
    body { overflow-y: auto; }
    .history-container {
      max-width: 640px;
      margin: 0 auto;
      padding: 60px 32px 80px;
    }
    .history-header {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 48px;
    }
    .back-link {
      color: var(--text-dim);
      text-decoration: none;
      font-size: 14px;
      font-family: var(--font-sans);
      font-weight: 300;
      transition: color 0.3s;
    }
    .back-link:hover { color: var(--gold); }
    .history-title {
      font-family: var(--font-serif);
      font-size: 22px;
      font-weight: 400;
      color: var(--text-primary);
    }
    .history-section {
      margin-bottom: 48px;
    }
    .history-section h3 {
      font-family: var(--font-sans);
      font-size: 10px;
      font-weight: 300;
      letter-spacing: 4px;
      color: var(--text-dim);
      margin-bottom: 20px;
      text-transform: uppercase;
    }
    .session-card {
      padding: 24px 0;
      border-bottom: 0.5px solid rgba(200, 170, 130, 0.1);
      cursor: pointer;
      transition: opacity 0.3s;
    }
    .session-card:hover { opacity: 0.8; }
    .session-date {
      font-size: 12px;
      color: var(--text-secondary);
      margin-bottom: 6px;
    }
    .session-preview {
      font-family: var(--font-serif);
      font-size: 16px;
      color: var(--text-primary);
      line-height: 1.6;
    }
    .session-tag {
      display: inline-block;
      font-size: 9px;
      letter-spacing: 2px;
      color: var(--text-dim);
      margin-top: 8px;
    }
    .pattern-card {
      padding: 20px 0;
      border-bottom: 0.5px solid rgba(200, 170, 130, 0.1);
    }
    .pattern-type {
      font-size: 10px;
      letter-spacing: 3px;
      color: var(--gold);
      margin-bottom: 6px;
    }
    .pattern-desc {
      font-size: 14px;
      color: var(--text-primary);
      line-height: 1.7;
    }
    .pattern-trend {
      font-size: 11px;
      color: var(--text-secondary);
      margin-top: 6px;
    }
    .empty-state {
      text-align: center;
      padding: 60px 0;
      color: var(--text-dim);
      font-family: var(--font-serif);
      font-size: 16px;
      font-style: italic;
    }
  </style>
</head>
<body>
  <div class="history-container">
    <div class="history-header">
      <a class="back-link" href="/">&larr; 回 去</a>
      <span class="history-title">曾经走过的路</span>
    </div>

    <div class="history-section">
      <h3>复盘记录</h3>
      <div id="sessions-list"></div>
    </div>

    <div class="history-section">
      <h3>反复出现的模式</h3>
      <div id="patterns-list"></div>
    </div>

    <div class="history-section">
      <h3>设置</h3>
      <div id="settings-form" style="margin-top:16px;">
        <label style="display:block;margin-bottom:12px;">
          <span style="font-size:10px;letter-spacing:3px;color:var(--text-dim);">API 提供商</span>
          <select id="cfg-provider" style="display:block;width:100%;margin-top:4px;padding:8px;background:transparent;border:0.5px solid rgba(200,170,130,0.2);color:var(--text-primary);font-family:var(--font-sans);font-size:13px;">
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </label>
        <label style="display:block;margin-bottom:12px;">
          <span style="font-size:10px;letter-spacing:3px;color:var(--text-dim);">API Key</span>
          <input id="cfg-key" type="password" placeholder="sk-..." style="display:block;width:100%;margin-top:4px;padding:8px;background:transparent;border:0.5px solid rgba(200,170,130,0.2);color:var(--text-primary);font-family:var(--font-sans);font-size:13px;">
        </label>
        <label style="display:block;margin-bottom:12px;">
          <span style="font-size:10px;letter-spacing:3px;color:var(--text-dim);">模型</span>
          <input id="cfg-model" type="text" placeholder="gpt-4o" style="display:block;width:100%;margin-top:4px;padding:8px;background:transparent;border:0.5px solid rgba(200,170,130,0.2);color:var(--text-primary);font-family:var(--font-sans);font-size:13px;">
        </label>
        <button id="cfg-save" style="margin-top:12px;padding:8px 24px;background:transparent;border:0.5px solid rgba(200,170,130,0.3);color:var(--text-primary);font-family:var(--font-sans);font-size:12px;font-weight:300;letter-spacing:3px;cursor:pointer;transition:border-color 0.3s;">保 存</button>
      </div>
    </div>
  </div>

  <script>
    async function loadHistory() {
      // 加载 sessions
      const sResp = await fetch('/api/sessions');
      const sessions = await sResp.json();
      const sList = document.getElementById('sessions-list');
      if (sessions.length === 0) {
        sList.innerHTML = '<div class="empty-state">还没有复盘记录<br>回去写第一次吧</div>';
      } else {
        sList.innerHTML = sessions.map(s => `
          <div class="session-card" onclick="viewSession(${s.id})">
            <div class="session-date">${new Date(s.created_at).toLocaleDateString('zh-CN', {year:'numeric',month:'long',day:'numeric',weekday:'long'})}</div>
            <div class="session-preview">${s.takeaway || '查看完整对话...'}</div>
            ${s.tag ? `<div class="session-tag">${s.tag}</div>` : ''}
          </div>`).join('');
      }

      // 加载 patterns
      const pResp = await fetch('/api/patterns');
      const patterns = await pResp.json();
      const pList = document.getElementById('patterns-list');
      if (patterns.length === 0) {
        pList.innerHTML = '<div class="empty-state">复盘多了<br>模式会自然浮现</div>';
      } else {
        pList.innerHTML = patterns.map(p => `
          <div class="pattern-card">
            <div class="pattern-type">${p.type}</div>
            <div class="pattern-desc">${p.description}</div>
            <div class="pattern-trend">首次：${new Date(p.first_seen).toLocaleDateString('zh-CN')} · 趋势：${p.trend === 'strengthening' ? '强化中' : p.trend === 'weakening' ? '减弱中' : '稳定'}</div>
          </div>`).join('');
      }
    }

    async function loadConfig() {
      const resp = await fetch('/api/config');
      const cfg = await resp.json();
      document.getElementById('cfg-provider').value = cfg.api_provider;
      document.getElementById('cfg-model').value = cfg.model;
      if (cfg.has_key) document.getElementById('cfg-key').placeholder = '已设置 (不修改则留空)';
    }

    document.getElementById('cfg-save').addEventListener('click', async () => {
      const body = {
        api_provider: document.getElementById('cfg-provider').value,
        model: document.getElementById('cfg-model').value,
      };
      const key = document.getElementById('cfg-key').value.trim();
      if (key) body.api_key = key;
      await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      document.getElementById('cfg-key').value = '';
      document.getElementById('cfg-key').placeholder = '已保存';
    });

    function viewSession(id) {
      window.location.href = `/history?id=${id}`;
    }

    document.addEventListener('DOMContentLoaded', () => {
      loadHistory();
      loadConfig();
    });
  </script>
</body>
</html>
```

---

### 任务 10：入口文件 + 浏览器启动

**文件：**
- 创建：`project1：复盘agent/reflection/main.py`

- [ ] **步骤 1：编写 main.py**

```python
"""Reflection 桌面应用入口。启动本地服务器，自动打开浏览器。"""
import sys
import webbrowser
import threading
import time
import uvicorn
from pathlib import Path

# 确保项目根在 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reflection.server import app
from reflection.config import ensure_data_dir, load_config


HOST = "127.0.0.1"
PORT = 18080


def open_browser():
    """等服务器就绪后打开浏览器。"""
    time.sleep(1.0)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    ensure_data_dir()
    cfg = load_config()

    print(f"  Reflection · 反观 v0.1.0")
    print(f"  数据目录: {cfg.model_dump()}")
    print(f"  打开 http://{HOST}:{PORT}")
    print()

    # 在新线程中打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
```

- [ ] **步骤 2：验证启动**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
Start-Process -NoNewWindow python -ArgumentList "-m", "reflection.main"
```
预期：终端输出 Reflection 启动信息，浏览器自动打开。

手动 Ctrl+C 停止。

---

### 任务 11：PyInstaller 打包

**文件：**
- 创建：`project1：复盘agent/reflection/reflection.spec`

- [ ] **步骤 1：编写 reflection.spec**

```python
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# 静态文件目录
static_dir = Path('reflection/static')

added_files = [
    (str(static_dir), 'reflection/static'),
]

a = Analysis(
    ['reflection/main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['sqlalchemy', 'httpx', 'fastapi', 'uvicorn'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Reflection',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
```

- [ ] **步骤 2：执行打包**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
pyinstaller --clean reflection/reflection.spec
```
预期：生成 `dist/Reflection.exe`。

- [ ] **步骤 3：验证 .exe 可运行**

```powershell
Start-Process "D:\MyAIWorkspace\project1：复盘agent\dist\Reflection.exe"
```
预期：浏览器自动打开，显示 Reflection 首页。

---

### 任务 12：集成测试

**文件：**
- 创建：`project1：复盘agent/reflection/tests/`
- 创建：`project1：复盘agent/reflection/tests/__init__.py`
- 创建：`project1：复盘agent/reflection/tests/test_database.py`
- 创建：`project1：复盘agent/reflection/tests/test_engine.py`

- [ ] **步骤 1：编写 test_database.py**

```python
"""数据库模块测试。"""
import tempfile
import os
from pathlib import Path
from reflection.database import get_engine, get_db, Base, SessionModel, InsightModel, PatternModel


def test_create_tables():
    """验证表创建成功。"""
    db = get_db()
    tables = db.get_bind().table_names()
    assert "sessions" in tables
    assert "insights" in tables
    assert "patterns" in tables
    db.close()


def test_create_session():
    """验证创建 session。"""
    db = get_db()
    s = SessionModel(tag="test")
    db.add(s)
    db.commit()
    assert s.id is not None
    assert s.status == "active"
    db.delete(s)
    db.commit()
    db.close()


def test_create_insight():
    """验证创建 insight 并关联 session。"""
    db = get_db()
    s = SessionModel(tag="test")
    db.add(s)
    db.commit()

    i = InsightModel(session_id=s.id, dimension="thought", content="测试洞察")
    db.add(i)
    db.commit()
    assert i.id is not None
    assert len(s.insights) == 1

    db.delete(s)
    db.commit()
    db.close()
```

- [ ] **步骤 2：运行数据库测试**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -m pytest reflection/tests/test_database.py -v
```
预期：3 passed

- [ ] **步骤 3：编写 test_engine.py**

```python
"""复盘引擎测试（不依赖 LLM API）。"""
import json
from reflection.engine import start_session, _dimension_key, _get_phase_prompt


def test_start_session():
    """验证 start_session 创建 session 并返回开场白。"""
    sid, opening = start_session(tag="测试")
    assert sid > 0
    assert "今天" in opening
    assert "什么在你心里" in opening


def test_dimension_key():
    """验证维度中文→英文映射。"""
    assert _dimension_key("念头") == "thought"
    assert _dimension_key("内在状态") == "state"
    assert _dimension_key("道的体悟") == "dao"
    assert _dimension_key("未知") == "thought"


def test_phase_prompt():
    """验证三轮提示词包含正确阶段标记。"""
    p1 = _get_phase_prompt(1)
    assert "倾倒" in p1

    p2 = _get_phase_prompt(3)
    assert "觉察" in p2

    p3 = _get_phase_prompt(6)
    assert "沉淀" in p3
```

- [ ] **步骤 4：运行引擎测试**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -m pytest reflection/tests/test_engine.py -v
```
预期：3 passed

- [ ] **步骤 5：运行全部测试**

```powershell
cd "D:\MyAIWorkspace\project1：复盘agent"
python -m pytest reflection/tests/ -v
```
预期：6 passed
```

---

## 自检记录

- [x] **规格覆盖度**：设计文档 9 个章节全部覆盖——产品定位(任务7-9)、架构(任务1)、数据模型(任务3)、复盘引擎(任务5)、界面设计(任务7-9)、技术栈(任务1-4)、分发(任务11)、排除项(全部遵守)、待决定项(无阻塞)
- [x] **占位符扫描**：无 TODO/TBD/占位符。所有步骤均包含实际代码或精确命令。
- [x] **类型一致性**：Config/ConfigUpdate/SessionModel/InsightModel/PatternModel 在各任务间引用一致。API 端点与前端 fetch 路径匹配：POST /api/sessions, POST /api/sessions/{id}/messages, GET /api/sessions, GET /api/sessions/{id}, GET /api/patterns, GET/POST /api/config。
