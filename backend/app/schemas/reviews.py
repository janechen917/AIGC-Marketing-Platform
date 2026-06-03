"""批量好评生成 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("product_name", "platform", "style")
    @classmethod
    def _strip_required_str(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("字段不能为空")
        return cleaned

    @field_validator("selling_points")
    @classmethod
    def _clean_selling_points(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("selling_points 至少包含一条有效卖点")
        return cleaned

    @field_validator("persona_pool")
    @classmethod
    def _clean_persona_pool(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = item.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            cleaned.append(text)
        return cleaned


class ReviewsGenerateResponse(BaseModel):
    reviews: list[str]
    total_generated: int
    rounds: int
    deduped_dropped: int
    compliance_dropped: int = 0
    csv_content: str
