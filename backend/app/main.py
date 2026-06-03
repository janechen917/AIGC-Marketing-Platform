"""FastAPI 入口。

当前阶段（STEP 11 第一版）提供：
- GET  /         应用元信息
- GET  /health   检查后端 + Postgres + Redis 连通性
- POST /api/auth/register   注册
- POST /api/auth/login      登录（OAuth2 表单，返回 JWT）
- GET  /api/auth/me         当前用户信息
- POST /api/compliance/check 规则审核（敏感词/广告法/品牌/格式）
- POST /api/copy/generate   广告文案生成（DeepSeek-V4 初稿 + Qwen3.7-Max 润色）
- POST /api/reviews/generate 批量好评生成（人设池 + 去重阈值）
- POST /api/poster/generate 海报生成（异步 + MinIO）
- GET  /api/poster/{id}     查询海报任务
- POST /api/video/start     视频生成任务启动
- GET  /api/video/{id}      查询视频任务
- POST /api/video/confirm   确认进入下一阶段
- POST /api/tasks/ping      异步任务连通性测试
- GET  /api/tasks/{task_id} 查询任务状态

后续 STEP 会继续增强视频模型与 RAG 能力。
"""
import redis
from fastapi import FastAPI
from loguru import logger
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.copywriter import router as copywriter_router
from app.api.compliance import router as compliance_router
from app.api.poster import router as poster_router
from app.api.reviews import router as reviews_router
from app.api.tasks import router as tasks_router
from app.api.video import router as video_router
from app.core.config import settings
from app.core.db import engine

app = FastAPI(
    title="AIGC Marketing Platform API",
    version="0.2.0",
    description="个人/小团队 AIGC 营销内容生成平台",
)

app.include_router(auth_router)
app.include_router(copywriter_router)
app.include_router(compliance_router)
app.include_router(poster_router)
app.include_router(reviews_router)
app.include_router(video_router)
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
