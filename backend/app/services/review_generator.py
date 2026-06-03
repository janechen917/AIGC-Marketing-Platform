"""批量好评生成服务（STEP 8）。"""

from __future__ import annotations

import csv
import io
import random
import re
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.generation_log import GenerationLog
from app.schemas.reviews import ReviewsGenerateRequest, ReviewsGenerateResponse
from app.services.compliance import check_all
from app.services.llm_router import llm_router

PROMPT_FILE = Path(__file__).resolve().parents[1] / "prompts" / "reviews" / "generate.md"
DEFAULT_PROMPT = "请生成 {count} 条好评文案，每行一条。"


def _load_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8")
    return DEFAULT_PROMPT


def _normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^[\-\*\d\.、\)\s]+", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def _extract_candidates(raw_text: str) -> list[str]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    cleaned: list[str] = []
    for line in lines:
        item = _normalize_text(line)
        if item:
            cleaned.append(item)
    return cleaned


def _is_similar(a: str, b: str, threshold: float) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= threshold


def _to_csv(reviews: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["review"])
    for review in reviews:
        writer.writerow([review])
    return buffer.getvalue()


def _write_generation_log(
    db: Session,
    *,
    user_id: int,
    model_used: str,
    prompt_tokens: int,
    completion_tokens: int,
    input_data: dict,
    output_data: dict,
) -> None:
    db.add(
        GenerationLog(
            user_id=user_id,
            module="review",
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            input_data=input_data,
            output_data=output_data,
        )
    )
    db.commit()


def generate_reviews(
    *,
    req: ReviewsGenerateRequest,
    db: Session,
    user_id: int,
) -> ReviewsGenerateResponse:
    template = _load_prompt()

    if not req.persona_pool:
        req.persona_pool = ["普通用户"]

    reviews: list[str] = []
    deduped_dropped = 0
    rounds = 0

    personas = req.persona_pool[:]
    random.shuffle(personas)

    while len(reviews) < req.target_count and rounds < req.max_rounds:
        persona = personas[rounds % len(personas)]
        rounds += 1

        prompt = template.format(
            count=req.batch_size,
            persona=persona,
            product_name=req.product_name,
            selling_points="；".join(req.selling_points),
            platform=req.platform,
            style=req.style,
        )

        messages = [
            {"role": "system", "content": "你是社媒口碑文案生成助手，输出短评列表。"},
            {"role": "user", "content": prompt},
        ]

        result = llm_router.chat(
            messages=messages,
            model=settings.COPY_POLISH_MODEL,
            module="review",
            db=db,
            user_id=user_id,
            temperature=0.85,
            max_tokens=1200,
        )

        candidates = _extract_candidates(result.text)

        accepted_now: list[str] = []
        for item in candidates:
            if any(_is_similar(item, existing, req.similarity_threshold) for existing in reviews):
                deduped_dropped += 1
                continue

            compliance = check_all(
                item,
                require_hashtag=req.require_hashtag,
                require_cta=req.require_cta,
            )
            if not compliance["passed"]:
                deduped_dropped += 1
                continue

            reviews.append(item)
            accepted_now.append(item)
            if len(reviews) >= req.target_count:
                break

        _write_generation_log(
            db,
            user_id=user_id,
            model_used=result.model_used,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            input_data={
                "round": rounds,
                "persona": persona,
                "prompt": prompt,
                "batch_size": req.batch_size,
            },
            output_data={
                "raw_text": result.text,
                "accepted": accepted_now,
            },
        )

    reviews = reviews[: req.target_count]
    return ReviewsGenerateResponse(
        reviews=reviews,
        total_generated=len(reviews),
        rounds=rounds,
        deduped_dropped=deduped_dropped,
        csv_content=_to_csv(reviews),
    )
