"""Reflection 桌面应用入口。启动本地服务器，自动打开浏览器。"""
import sys
import webbrowser
import threading
import time
import uvicorn
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from reflection.server import app
from reflection.config import ensure_data_dir, load_config


HOST = "127.0.0.1"
PORT = 18080


def open_browser():
    time.sleep(1.0)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    ensure_data_dir()
    cfg = load_config()

    print(f"  Reflection · 反观 v0.1.0")
    print(f"  数据目录: {cfg.model_dump()}")
    print(f"  打开 http://{HOST}:{PORT}")
    print()

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
