"""品牌合规审核。"""

from __future__ import annotations


def check_brand_rules(
    text: str,
    *,
    brand_name: str | None = None,
    required_phrases: list[str] | None = None,
    forbidden_competitors: list[str] | None = None,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    if brand_name and brand_name not in text:
        issues.append(
            {
                "rule": "brand",
                "message": f"未提及品牌名: {brand_name}",
                "level": "warning",
            }
        )

    if required_phrases:
        missing = [phrase for phrase in required_phrases if phrase and phrase not in text]
        if missing:
            issues.append(
                {
                    "rule": "brand",
                    "message": f"缺少必含短语: {', '.join(missing)}",
                    "level": "warning",
                }
            )

    if forbidden_competitors:
        hits = sorted({name for name in forbidden_competitors if name and name in text})
        if hits:
            issues.append(
                {
                    "rule": "brand",
                    "message": f"命中禁用竞品词: {', '.join(hits)}",
                    "level": "error",
                }
            )

    return issues
