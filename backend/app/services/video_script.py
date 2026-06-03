"""视频脚本生成服务（STEP 10.1）。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.llm_router import llm_router
from app.services.rag_retriever import retrieve_context


@dataclass
class ScriptGenerationResult:
    script_data: dict[str, Any]
    model_used: str
    prompt_tokens: int
    completion_tokens: int


def _extract_json_object(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text)
    candidate = fenced.group(1) if fenced else text
    candidate = candidate.strip()

    # 尝试直接 JSON 解析；失败后截取首个大括号块。
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start >= 0 and end > start:
        parsed = json.loads(candidate[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("无法从模型返回中解析脚本 JSON")


def _normalize_script(payload: dict[str, Any], shot_count: int) -> dict[str, Any]:
    title = str(payload.get("title") or "AI 短视频脚本")
    narration = str(payload.get("narration") or "")
    raw_shots = payload.get("shots")
    if not isinstance(raw_shots, list):
        raw_shots = []

    shots: list[dict[str, Any]] = []
    for i in range(shot_count):
        item = raw_shots[i] if i < len(raw_shots) and isinstance(raw_shots[i], dict) else {}
        scene_desc = str(item.get("scene_desc") or f"镜头{i + 1}：围绕主题展开")
        duration = item.get("duration_sec")
        try:
            duration_sec = int(duration)
        except Exception:
            duration_sec = 3
        shots.append({"index": i + 1, "scene_desc": scene_desc, "duration_sec": max(1, duration_sec)})

    return {"title": title, "narration": narration, "shots": shots}


def generate_video_script(
    *,
    prompt: str,
    shot_count: int,
    db: Session,
    user_id: int | None,
) -> ScriptGenerationResult:
    rag_context = retrieve_context(prompt, top_k=3)

    user_prompt = (
        "你是短视频导演与脚本策划。请基于用户主题输出严格 JSON，不要输出任何解释。\n"
        "JSON schema: {\"title\": string, \"narration\": string, "
        "\"shots\": [{\"index\": number, \"scene_desc\": string, \"duration_sec\": number}]}\n"
        f"要求镜头数: {shot_count}\n"
        "每个镜头 scene_desc 要包含可直接用于文生图的画面描述。\n"
        f"用户主题: {prompt}\n"
        f"可参考知识上下文（可选）:\n{rag_context if rag_context else '(无)'}"
    )

    result = llm_router.chat(
        messages=[
            {"role": "system", "content": "你是专业广告短视频策划，请只输出 JSON。"},
            {"role": "user", "content": user_prompt},
        ],
        model=settings.VIDEO_DEEPSEEK_MODEL,
        module="video",
        db=db,
        user_id=user_id,
        temperature=0.4,
        max_tokens=1800,
    )

    parsed = _extract_json_object(result.text)
    normalized = _normalize_script(parsed, shot_count)
    return ScriptGenerationResult(
        script_data=normalized,
        model_used=result.model_used,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
    )
