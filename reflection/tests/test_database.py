"""数据库模块测试。"""
from reflection.database import get_db, SessionModel, InsightModel


def test_create_tables():
    """验证表创建成功。"""
    db = get_db()
    from sqlalchemy import inspect
    tables = inspect(db.get_bind()).get_table_names()
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
