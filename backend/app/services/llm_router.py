"""统一模型路由层（STEP 4）。

当前实现：
- 文本模型：DashScope OpenAI-compatible chat/completions
- 统一入口：LLMRouter.chat(...)
- 能力：超时、重试、错误归一化、token/成本记录（usage_logs）
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.usage_log import UsageLog


class LLMRouterError(RuntimeError):
    """模型调用失败（统一异常类型）。"""


@dataclass
class ChatResult:
    """LLM 文本输出结果。"""

    text: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    raw: dict[str, Any]


class LLMRouter:
    """统一模型调用入口。"""

    def __init__(self) -> None:
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.default_timeout = 60
        self.max_retries = 2

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str,
        module: str,
        db: Session | None = None,
        user_id: int | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1200,
        timeout: int | None = None,
    ) -> ChatResult:
        """调用文本模型并返回标准化结果。"""
        if not settings.DASHSCOPE_API_KEY:
            raise LLMRouterError("DASHSCOPE_API_KEY 未配置")
        if not messages:
            raise LLMRouterError("messages 不能为空")

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp_json = self._post_with_retry(
            url=f"{self.base_url}/chat/completions",
            payload=payload,
            timeout=timeout or self.default_timeout,
        )

        result = self._normalize_chat_response(resp_json)

        if db is not None:
            self._write_usage_log(
                db=db,
                module=module,
                model_used=result.model_used,
                tokens_used=result.total_tokens,
                user_id=user_id,
            )

        return result

    def _post_with_retry(
        self,
        *,
        url: str,
        payload: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 2):
            try:
                req = request.Request(
                    url=url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
                    },
                    method="POST",
                )
                with request.urlopen(req, timeout=timeout) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body)
            except error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="ignore")
                last_exc = LLMRouterError(f"DashScope HTTP {exc.code}: {body}")
                logger.warning(f"LLM request failed attempt={attempt}: {last_exc}")
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                logger.warning(f"LLM request failed attempt={attempt}: {exc}")

            if attempt <= self.max_retries:
                # 简单指数退避：1s, 2s
                time.sleep(2 ** (attempt - 1))

        raise LLMRouterError(f"模型调用失败: {last_exc}")

    def _normalize_chat_response(self, resp: dict[str, Any]) -> ChatResult:
        choices = resp.get("choices") or []
        if not choices:
            raise LLMRouterError(f"无有效 choices: {resp}")

        message = choices[0].get("message") or {}
        content = message.get("content", "")

        if isinstance(content, list):
            # 兼容分块 content 场景
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(str(item.get("text", "")))
            text = "".join(text_parts).strip()
        else:
            text = str(content).strip()

        usage = resp.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))
        total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))

        model_used = str(resp.get("model") or "unknown")

        return ChatResult(
            text=text,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            raw=resp,
        )

    def _write_usage_log(
        self,
        *,
        db: Session,
        module: str,
        model_used: str,
        tokens_used: int,
        user_id: int | None,
    ) -> None:
        # 先用保守估算：¥0.02 / 1k tokens，后续可按模型细分价格表。
        cost_cny = (tokens_used / 1000.0) * 0.02
        db.add(
            UsageLog(
                user_id=user_id,
                module=module,
                model_used=model_used,
                tokens_used=tokens_used,
                cost_cny=round(cost_cny, 6),
            )
        )
        db.commit()


llm_router = LLMRouter()
