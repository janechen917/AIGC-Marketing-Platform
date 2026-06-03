"""规则审核 API 的请求/响应 Schema。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ComplianceCheckRequest(BaseModel):
    text: str = Field(min_length=1)

    brand_name: str | None = None
    required_phrases: list[str] = Field(default_factory=list)
    forbidden_competitors: list[str] = Field(default_factory=list)

    max_length: int | None = None
    require_hashtag: bool = False
    require_cta: bool = False
    max_emojis: int | None = None

    ad_law_extra_banned_words: list[str] = Field(default_factory=list)


class ComplianceIssue(BaseModel):
    rule: str
    message: str
    level: str


class ComplianceCheckResponse(BaseModel):
    passed: bool
    issue_count: int
    issues: list[ComplianceIssue]
