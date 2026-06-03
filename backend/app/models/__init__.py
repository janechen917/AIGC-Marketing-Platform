"""ORM 模型统一导入入口。

所有模型必须在这里 import，Alembic autogenerate 才能检测到。
"""
from app.core.db import Base  # noqa: F401
from app.models.generation_log import GenerationLog  # noqa: F401
from app.models.poster_task import PosterTask  # noqa: F401
from app.models.usage_log import UsageLog  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.video_task import VideoTask  # noqa: F401

__all__ = [
	"Base",
	"User",
	"GenerationLog",
	"UsageLog",
	"PosterTask",
	"VideoTask",
]
