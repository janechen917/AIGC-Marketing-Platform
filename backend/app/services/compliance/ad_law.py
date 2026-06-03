"""广告法违禁词审核。"""

from __future__ import annotations

DEFAULT_BANNED_WORDS: tuple[str, ...] = (
    "最佳",
    "第一",
    "国家级",
    "最高级",
    "顶级",
    "绝对",
    "100%",
    "永久",
    "无副作用",
)


def check_ad_law_words(text: str, extra_banned_words: list[str] | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    banned_words = list(DEFAULT_BANNED_WORDS)
    if extra_banned_words:
        banned_words.extend([w for w in extra_banned_words if w])

    hit_words = sorted({word for word in banned_words if word in text})
    if hit_words:
        issues.append(
            {
                "rule": "ad_law",
                "message": f"命中广告法违禁词: {', '.join(hit_words)}",
                "level": "error",
            }
        )
    return issues
