"""广告文案业务逻辑（STEP 7）。"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.generation_log import GenerationLog
from app.schemas.copywriter import CopyGenerateRequest, CopyGenerateResponse
from app.schemas.compliance import ComplianceCheckResponse
from app.services.compliance import check_all
from app.services.llm_router import llm_router

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts" / "copywriter"
DRAFT_PROMPT_FILE = PROMPT_DIR / "draft.md"
POLISH_PROMPT_FILE = PROMPT_DIR / "polish.md"

DEFAULT_DRAFT_PROMPT = "请先输出结构化营销框架，再给文案初稿。"
DEFAULT_POLISH_PROMPT = "请把以下初稿润色为专业中文营销文案：\n{draft_text}"


def _load_prompt(path: Path, fallback: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return fallback


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
            module="copy",
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            input_data=input_data,
            output_data=output_data,
        )
    )
    db.commit()


def generate_copy(
    *,
    req: CopyGenerateRequest,
    db: Session,
    user_id: int,
) -> CopyGenerateResponse:
    draft_template = _load_prompt(DRAFT_PROMPT_FILE, DEFAULT_DRAFT_PROMPT)
    polish_template = _load_prompt(POLISH_PROMPT_FILE, DEFAULT_POLISH_PROMPT)

    draft_prompt = draft_template.format(
        product_name=req.product_name,
        selling_points="；".join(req.selling_points),
        target_audience=req.target_audience,
        platform=req.platform,
        style=req.style,
        length_hint=req.length_hint,
        title_count=req.title_count,
    )

    draft_messages = [
        {"role": "system", "content": "你是营销策划专家，输出结构清晰、信息充分。"},
        {"role": "user", "content": draft_prompt},
    ]

    draft_result = llm_router.chat(
        messages=draft_messages,
        model=settings.COPY_DRAFT_MODEL,
        module="copy",
        db=db,
        user_id=user_id,
        temperature=0.4,
        max_tokens=1200,
    )

    _write_generation_log(
        db,
        user_id=user_id,
        model_used=draft_result.model_used,
        prompt_tokens=draft_result.prompt_tokens,
        completion_tokens=draft_result.completion_tokens,
        input_data={"stage": "draft", "prompt": draft_prompt},
        output_data={"text": draft_result.text},
    )

    polish_prompt = polish_template.format(draft_text=draft_result.text)
    polish_messages = [
        {"role": "system", "content": "你是中文文案润色专家，输出可直接发布内容。"},
        {"role": "user", "content": polish_prompt},
    ]

    polish_result = llm_router.chat(
        messages=polish_messages,
        model=settings.COPY_POLISH_MODEL,
        module="copy",
        db=db,
        user_id=user_id,
        temperature=0.7,
        max_tokens=1200,
    )

    _write_generation_log(
        db,
        user_id=user_id,
        model_used=polish_result.model_used,
        prompt_tokens=polish_result.prompt_tokens,
        completion_tokens=polish_result.completion_tokens,
        input_data={"stage": "polish", "prompt": polish_prompt},
        output_data={"text": polish_result.text},
    )

    compliance_result = check_all(
        polish_result.text,
        brand_name=req.brand_name,
        required_phrases=req.required_phrases,
        forbidden_competitors=req.forbidden_competitors,
        max_length=req.max_length,
        require_hashtag=req.require_hashtag,
        require_cta=req.require_cta,
        max_emojis=req.max_emojis,
    )

    return CopyGenerateResponse(
        draft_text=draft_result.text,
        polished_text=polish_result.text,
        draft_model=draft_result.model_used,
        polish_model=polish_result.model_used,
        compliance=ComplianceCheckResponse(**compliance_result),
    )
