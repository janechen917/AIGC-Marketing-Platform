"""格式规范审核。"""

from __future__ import annotations

import re

CTA_HINTS: tuple[str, ...] = (
    "立即",
    "马上",
    "点击",
    "咨询",
    "抢购",
    "购买",
    "下单",
    "预约",
    "了解更多",
)

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA70-\U0001FAFF"
    "]",
    flags=re.UNICODE,
)


def check_format_rules(
    text: str,
    *,
    max_length: int | None = None,
    require_hashtag: bool = False,
    require_cta: bool = False,
    max_emojis: int | None = None,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if max_length is not None and len(text) > max_length:
        issues.append(
            {
                "rule": "format",
                "message": f"内容长度超限: {len(text)} > {max_length}",
                "level": "warning",
            }
        )

    if require_hashtag and "#" not in text:
        issues.append(
            {
                "rule": "format",
                "message": "缺少 Hashtag (#)",
                "level": "warning",
            }
        )

    if require_cta and not any(hint in text for hint in CTA_HINTS):
        issues.append(
            {
                "rule": "format",
                "message": "缺少 CTA 引导语（如: 立即、点击、咨询）",
                "level": "warning",
            }
        )

    if max_emojis is not None:
        emoji_count = len(EMOJI_PATTERN.findall(text))
        if emoji_count > max_emojis:
            issues.append(
                {
                    "rule": "format",
                    "message": f"Emoji 数量超限: {emoji_count} > {max_emojis}",
                    "level": "warning",
                }
            )

    return issues
