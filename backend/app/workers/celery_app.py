"""Celery 应用入口（STEP 5）。

运行方式：
    uv run celery -A app.workers.celery_app:celery_app worker -l info
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "aigc_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.poster_worker",
        "app.workers.video_worker",
    ],
)

celery_app.conf.update(
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_default_queue=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
)


@celery_app.task(name="app.workers.ping")
def ping_task() -> dict[str, str]:
    """最小连通性任务：用于验证 worker 链路。"""
    return {"message": "pong"}
