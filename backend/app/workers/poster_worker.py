"""海报任务占位 worker。"""

from typing import Any

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="app.workers.poster.generate")
def generate_poster_task(self, payload: dict[str, Any]) -> dict[str, Any]:
    """海报生成任务占位实现，STEP 7+ 替换为真实逻辑。"""
    shot_count = int(payload.get("shot_count", 1))
    return {
        "status": "ok",
        "task": "poster.generate",
        "shot_count": shot_count,
        "note": "placeholder",
    }
