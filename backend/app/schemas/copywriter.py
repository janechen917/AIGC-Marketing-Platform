"""广告文案生成 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.compliance import ComplianceCheckResponse


class CopyGenerateRequest(BaseModel):
    product_name: str = Field(min_length=1)
    selling_points: list[str] = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    style: str = "专业"
    length_hint: str = "中等"
    title_count: int = Field(default=3, ge=1, le=8)

    brand_name: str | None = None
    required_phrases: list[str] = Field(default_factory=list)
    forbidden_competitors: list[str] = Field(default_factory=list)
    require_hashtag: bool = True
    require_cta: bool = True
    max_length: int | None = None
    max_emojis: int | None = 6


class CopyGenerateResponse(BaseModel):
    draft_text: str
    polished_text: str
    draft_model: str
    polish_model: str
    compliance: ComplianceCheckResponse
