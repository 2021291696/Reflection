"""FastAPI 服务器：REST API 路由。"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from .config import load_config, save_config
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


@app.post("/api/shutdown")
def api_shutdown():
    import os
    os._exit(0)


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
