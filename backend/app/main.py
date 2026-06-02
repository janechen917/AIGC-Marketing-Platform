"""FastAPI 入口。

当前阶段（STEP 5）提供：
- GET  /         应用元信息
- GET  /health   检查后端 + Postgres + Redis 连通性
- POST /api/auth/register   注册
- POST /api/auth/login      登录（OAuth2 表单，返回 JWT）
- GET  /api/auth/me         当前用户信息
- POST /api/tasks/ping      异步任务连通性测试
- GET  /api/tasks/{task_id} 查询任务状态

后续 STEP 会按需挂载 api/copywriter, api/poster, api/video 等路由。
"""
import redis
from fastapi import FastAPI
from loguru import logger
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.core.config import settings
from app.core.db import engine

app = FastAPI(
    title="AIGC Marketing Platform API",
    version="0.2.0",
    description="个人/小团队 AIGC 营销内容生成平台",
)

app.include_router(auth_router)
app.include_router(tasks_router)


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
    status_: dict[str, str] = {"api": "ok", "postgres": "unknown", "redis": "unknown"}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status_["postgres"] = "ok"
    except Exception as e:  # noqa: BLE001
        status_["postgres"] = f"error: {e.__class__.__name__}"
        logger.error(f"Postgres health check failed: {e}")

    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        status_["redis"] = "ok"
    except Exception as e:  # noqa: BLE001
        status_["redis"] = f"error: {e.__class__.__name__}"
        logger.error(f"Redis health check failed: {e}")

    return status_
