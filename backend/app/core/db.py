"""数据库连接与会话工厂。

- engine：SQLAlchemy 同步引擎（Postgres via psycopg3）
- SessionLocal：会话工厂，每个请求独立会话
- Base：所有 ORM 模型继承自此 DeclarativeBase
- get_db()：FastAPI Depends 注入用
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
