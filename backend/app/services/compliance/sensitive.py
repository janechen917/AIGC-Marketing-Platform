"""敏感词审核（文本词表匹配）。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

WORDLIST_PATH = Path(__file__).resolve().parent / "wordlists" / "sensitive.txt"


@lru_cache(maxsize=1)
def load_sensitive_words() -> tuple[str, ...]:
    if not WORDLIST_PATH.exists():
        return tuple()

    words: list[str] = []
    for raw in WORDLIST_PATH.read_text(encoding="utf-8").splitlines():
        word = raw.strip()
        if not word or word.startswith("#"):
            continue
        words.append(word)
    return tuple(words)


def check_sensitive_words(text: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    hit_words: list[str] = []

    for word in load_sensitive_words():
        if word in text:
            hit_words.append(word)

    if hit_words:
        issues.append(
            {
                "rule": "sensitive",
                "message": f"命中敏感词: {', '.join(sorted(set(hit_words)))}",
                "level": "error",
            }
        )
    return issues
