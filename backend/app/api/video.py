"""视频生成 API（STEP 10 第一版）。

- POST /api/video/start    创建任务 + 投递脚本阶段
- GET  /api/video/{id}     查询任务状态
- POST /api/video/confirm  确认进入下一阶段
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.video_task import VideoTask
from app.schemas.video import VideoConfirmRequest, VideoStartRequest, VideoTaskResponse
from app.workers.video_worker import generate_video_task

router = APIRouter(prefix="/api/video", tags=["video"])


@router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=VideoTaskResponse,
)
def start_video(
    req: VideoStartRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> VideoTaskResponse:
    video_id = uuid.uuid4().hex
    row = VideoTask(
        id=video_id,
        user_id=current_user.id,
        prompt=req.prompt,
        shot_count=req.shot_count,
        script_model=settings.VIDEO_DEEPSEEK_MODEL,
        image_model=settings.VIDEO_IMAGE_MODEL,
        clip_model=settings.VIDEO_CLIP_MODEL,
        status="pending",
        stage="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # 将 celery task_id 与 video_id 对齐，便于排查
    generate_video_task.apply_async(args=[video_id, "start", None], task_id=video_id)

    return VideoTaskResponse.model_validate(row, from_attributes=True)


@router.get("/{video_id}", response_model=VideoTaskResponse)
def get_video(
    video_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> VideoTaskResponse:
    row = db.get(VideoTask, video_id)
    if row is None:
        raise HTTPException(status_code=404, detail="video task not found")
    return VideoTaskResponse.model_validate(row, from_attributes=True)


@router.post("/confirm", status_code=status.HTTP_202_ACCEPTED, response_model=VideoTaskResponse)
def confirm_video_stage(
    req: VideoConfirmRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> VideoTaskResponse:
    row = db.get(VideoTask, req.video_id)
    if row is None:
        raise HTTPException(status_code=404, detail="video task not found")
    if row.stage != req.stage:
        raise HTTPException(
            status_code=409,
            detail=f"stage mismatch: current={row.stage}, expected={req.stage}",
        )

    action = "confirm_script" if req.stage == "script_done" else "confirm_images"
    row.status = "queued"
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)

    generate_video_task.delay(req.video_id, action, req.payload)

    return VideoTaskResponse.model_validate(row, from_attributes=True)
