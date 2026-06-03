"""视频生成任务表（STEP 10）。

stage 枚举：
pending -> script_done -> images_done -> done | failed
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class VideoTask(Base):
    __tablename__ = "video_tasks"

    # 与 celery task_id 一致的 uuid 字符串
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt: Mapped[str] = mapped_column(Text)
    shot_count: Mapped[int] = mapped_column(Integer, default=3)

    script_model: Mapped[str] = mapped_column(String(100))
    image_model: Mapped[str] = mapped_column(String(100))
    clip_model: Mapped[str] = mapped_column(String(100))

    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    stage: Mapped[str] = mapped_column(String(24), default="pending", index=True)

    script_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    image_urls: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    clip_urls: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    final_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
