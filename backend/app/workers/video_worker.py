"""视频任务占位 worker。"""

from typing import Any

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="app.workers.video.generate")
def generate_video_task(self, payload: dict[str, Any]) -> dict[str, Any]:
    """视频生成任务占位实现，STEP 9+ 替换为真实流水线。"""
    scene_count = int(payload.get("scene_count", 3))
    return {
        "status": "ok",
        "task": "video.generate",
        "scene_count": scene_count,
        "note": "placeholder",
    }
