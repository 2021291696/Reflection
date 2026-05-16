"""LLM API 抽象层：支持 DeepSeek、OpenAI 和 Anthropic。"""
import httpx
from .config import load_config

PROVIDER_DEFAULTS = {
    "deepseek": {"base": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "openai": {"base": "https://api.openai.com/v1", "model": "gpt-4o"},
    "anthropic": {"base": "", "model": "claude-sonnet-4-6"},
}


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
        return _chat_openai_compatible(cfg, messages)


def _chat_openai_compatible(cfg, messages: list[dict]) -> str:
    defaults = PROVIDER_DEFAULTS.get(cfg.api_provider, PROVIDER_DEFAULTS["openai"])
    base = cfg.api_base or defaults["base"]
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
