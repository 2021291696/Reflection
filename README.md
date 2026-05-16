# Reflection · 反观

一间安静的屋子，坐下来，和自己对话。

不局限于交易——生活、学习、关系，所有的经历都可以复盘。侧重心境、念头、道的层面。

## 安装

1. 解压 `Reflection-Setup.zip`
2. 双击 `安装.bat`
3. 双击桌面 `Reflection` 快捷方式
4. 点右上角小门 → 填 API Key → 回到首页开始

## 开发

```powershell
cd reflection
pip install -r requirements.txt
python -m reflection.main
```

浏览器自动打开 `http://127.0.0.1:18080`。

## 技术栈

Python 3.11+ · FastAPI · SQLite · 纯 HTML/CSS/JS · PyInstaller

## 测试

```powershell
pytest reflection/tests/ -v
```

## 设计

详见 `design.md`。
