"""异步任务 API（STEP 5）。"""

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, status

from app.workers.celery_app import celery_app, ping_task
from app.workers.poster_worker import generate_poster_task
from app.workers.video_worker import generate_video_task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/ping", status_code=status.HTTP_202_ACCEPTED)
def enqueue_ping() -> dict[str, str]:
    task = ping_task.delay()
    return {"task_id": task.id, "state": task.state, "task_name": "ping"}


@router.post("/poster-demo", status_code=status.HTTP_202_ACCEPTED)
def enqueue_poster_demo() -> dict[str, str]:
    task = generate_poster_task.delay({"shot_count": 1})
    return {"task_id": task.id, "state": task.state, "task_name": "poster.generate"}


@router.post("/video-demo", status_code=status.HTTP_202_ACCEPTED)
def enqueue_video_demo() -> dict[str, str]:
    task = generate_video_task.delay({"scene_count": 3})
    return {"task_id": task.id, "state": task.state, "task_name": "video.generate"}


@router.get("/{task_id}")
def get_task_status(task_id: str) -> dict[str, Any]:
    result = AsyncResult(task_id, app=celery_app)

    payload: dict[str, Any] = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else False,
    }

    if result.ready():
        if result.successful():
            payload["result"] = result.result
        else:
            payload["error"] = str(result.result)

    return payload
