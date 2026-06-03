"""规则审核引擎总入口。"""

from __future__ import annotations

from app.services.compliance.ad_law import check_ad_law_words
from app.services.compliance.brand import check_brand_rules
from app.services.compliance.format import check_format_rules
from app.services.compliance.sensitive import check_sensitive_words


def check_all(
    text: str,
    *,
    brand_name: str | None = None,
    required_phrases: list[str] | None = None,
    forbidden_competitors: list[str] | None = None,
    max_length: int | None = None,
    require_hashtag: bool = False,
    require_cta: bool = False,
    max_emojis: int | None = None,
    ad_law_extra_banned_words: list[str] | None = None,
) -> dict[str, object]:
    issues: list[dict[str, str]] = []

    issues.extend(check_sensitive_words(text))
    issues.extend(check_ad_law_words(text, extra_banned_words=ad_law_extra_banned_words))
    issues.extend(
        check_brand_rules(
            text,
            brand_name=brand_name,
            required_phrases=required_phrases,
            forbidden_competitors=forbidden_competitors,
        )
    )
    issues.extend(
        check_format_rules(
            text,
            max_length=max_length,
            require_hashtag=require_hashtag,
            require_cta=require_cta,
            max_emojis=max_emojis,
        )
    )

    return {
        "passed": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
    }
