"""SQLite 数据库：Session、Insight、Pattern 三张表。"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, create_engine, JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session as DBSession

from .config import DATA_DIR, ensure_data_dir

DB_PATH = DATA_DIR / "reflection.db"


def _now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=_now)
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
    created_at = Column(DateTime, default=_now)
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
