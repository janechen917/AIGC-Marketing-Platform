"""视频 API Schema（STEP 10）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class VideoStartRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    shot_count: int = Field(default=3, ge=1, le=12)


class VideoConfirmRequest(BaseModel):
    video_id: str
    stage: Literal["script_done", "images_done"]
    payload: dict[str, Any] | None = None


class VideoTaskResponse(BaseModel):
    id: str
    status: str
    stage: str
    prompt: str
    shot_count: int
    script_model: str
    image_model: str
    clip_model: str
    script_data: dict[str, Any] | None
    image_urls: list[str] | None
    clip_urls: list[str] | None
    final_video_url: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime
