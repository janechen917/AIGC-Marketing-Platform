"""轻量 RAG 检索服务（STEP 11 过渡版）。

当前实现基于本地文档语义片段匹配：
- docs/plan.md
- AI_GUIDE.md

后续可替换为 Qdrant 向量检索，不影响上层调用接口。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_SOURCES = [ROOT_DIR / "docs" / "plan.md", ROOT_DIR / "AI_GUIDE.md"]


@dataclass
class RetrievedChunk:
    score: int
    source: str
    text: str


def _tokenize(text: str) -> set[str]:
    # 英文词 + 数字 + 中文单字，足够支撑当前轻量检索。
    latin = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    return set(latin + cjk)


def _split_chunks(raw: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    return [p for p in parts if len(p) >= 20]


def retrieve_context(query: str, top_k: int = 3) -> str:
    """检索与 query 最相关的文档片段并拼接返回。"""
    q_tokens = _tokenize(query)
    if not q_tokens:
        return ""

    hits: list[RetrievedChunk] = []
    for src in DEFAULT_SOURCES:
        if not src.exists():
            continue
        raw = src.read_text(encoding="utf-8", errors="ignore")
        for chunk in _split_chunks(raw):
            c_tokens = _tokenize(chunk)
            score = len(q_tokens & c_tokens)
            if score > 0:
                hits.append(
                    RetrievedChunk(score=score, source=str(src.relative_to(ROOT_DIR)), text=chunk)
                )

    if not hits:
        return ""

    hits.sort(key=lambda x: x.score, reverse=True)
    selected = hits[: max(1, top_k)]

    blocks = []
    for h in selected:
        blocks.append(f"[source={h.source} score={h.score}]\n{h.text}")
    return "\n\n".join(blocks)
