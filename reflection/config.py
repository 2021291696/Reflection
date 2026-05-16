"""配置管理：API Key、模型选择、数据目录。"""
import json
import os
from pathlib import Path
from pydantic import BaseModel

DATA_DIR = Path(os.environ.get("REFLECTION_DATA", Path.home() / "Reflection"))
CONFIG_FILE = DATA_DIR / "config.json"


class Config(BaseModel):
    api_provider: str = "deepseek"     # deepseek / openai / anthropic
    api_key: str = ""
    model: str = "deepseek-chat"
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
