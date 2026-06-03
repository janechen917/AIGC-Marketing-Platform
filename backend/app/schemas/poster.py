"""海报 API Schema。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PosterGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)
    size: str | None = Field(default=None, description="如 1024*1024，留空走默认")


class PosterTaskResponse(BaseModel):
    id: str
    status: str
    prompt: str
    size: str
    model_used: str
    image_url: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime
