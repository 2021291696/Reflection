"""Reflection 桌面应用入口。启动本地服务器，自动打开浏览器。"""
import sys
import logging
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

# 先设好基础日志，避免 uvicorn 在无终端模式下崩溃
logging.basicConfig(level=logging.WARNING, format="%(message)s")


def open_browser():
    time.sleep(1.0)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    ensure_data_dir()
    load_config()

    threading.Thread(target=open_browser, daemon=True).start()

    # log_config=None 让 uvicorn 使用我们预先配好的 logging
    uvicorn.run(app, host=HOST, port=PORT, log_config=None)


if __name__ == "__main__":
    main()
