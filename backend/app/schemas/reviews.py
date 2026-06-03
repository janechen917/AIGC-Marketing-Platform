"""批量好评生成 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewsGenerateRequest(BaseModel):
    product_name: str = Field(min_length=1)
    selling_points: list[str] = Field(min_length=1)
    platform: str = Field(min_length=1)
    style: str = "真实口碑"

    target_count: int = Field(default=50, ge=1, le=100)
    batch_size: int = Field(default=8, ge=1, le=20)
    max_rounds: int = Field(default=20, ge=1, le=50)
    similarity_threshold: float = Field(default=0.85, ge=0.5, le=0.99)

    persona_pool: list[str] = Field(
        default_factory=lambda: ["宝妈", "学生", "上班族", "数码爱好者", "新手用户"]
    )

    require_hashtag: bool = False
    require_cta: bool = False


class ReviewsGenerateResponse(BaseModel):
    reviews: list[str]
    total_generated: int
    rounds: int
    deduped_dropped: int
    csv_content: str
