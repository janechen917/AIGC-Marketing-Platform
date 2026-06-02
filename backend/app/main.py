"""FastAPI 入口。

当前阶段（STEP 2）只提供：
- GET /         应用元信息
- GET /health   检查后端 + Postgres + Redis 连通性

后续 STEP 会按需挂载 api/auth, api/copywriter 等路由。
"""
import redis
from fastapi import FastAPI
from loguru import logger
from sqlalchemy import create_engine, text

from app.core.config import settings

app = FastAPI(
    title="AIGC Marketing Platform API",
    version="0.1.0",
    description="个人/小团队 AIGC 营销内容生成平台",
)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": "AIGC Marketing Platform",
        "version": app.version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    """检查 API / Postgres / Redis 连通性。"""
    status: dict[str, str] = {"api": "ok", "postgres": "unknown", "redis": "unknown"}

    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as e:  # noqa: BLE001
        status["postgres"] = f"error: {e.__class__.__name__}"
        logger.error(f"Postgres health check failed: {e}")

    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        status["redis"] = "ok"
    except Exception as e:  # noqa: BLE001
        status["redis"] = f"error: {e.__class__.__name__}"
        logger.error(f"Redis health check failed: {e}")

    return status
