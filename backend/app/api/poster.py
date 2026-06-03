"""海报生成 API（STEP 9）。

- POST /api/poster/generate  创建任务行 + 投递 Celery，返回 task_id
- GET  /api/poster/{poster_id}  查询任务状态（含 image_url）
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.poster_task import PosterTask
from app.models.user import User
from app.schemas.poster import PosterGenerateRequest, PosterTaskResponse
from app.workers.poster_worker import generate_poster_task

router = APIRouter(prefix="/api/poster", tags=["poster"])


@router.post(
    "/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PosterTaskResponse,
)
def enqueue_poster(
    req: PosterGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PosterTaskResponse:
    poster_id = uuid.uuid4().hex
    row = PosterTask(
        id=poster_id,
        user_id=current_user.id,
        prompt=req.prompt,
        size=req.size or settings.POSTER_IMAGE_SIZE,
        model_used=settings.POSTER_IMAGE_MODEL,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # 将 celery task_id 与 poster_id 对齐，方便日志/排查
    generate_poster_task.apply_async(args=[poster_id], task_id=poster_id)

    return PosterTaskResponse.model_validate(row, from_attributes=True)


@router.get("/{poster_id}", response_model=PosterTaskResponse)
def get_poster(
    poster_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> PosterTaskResponse:
    row = db.get(PosterTask, poster_id)
    if row is None:
        raise HTTPException(status_code=404, detail="poster not found")
    return PosterTaskResponse.model_validate(row, from_attributes=True)
