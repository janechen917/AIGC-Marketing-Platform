"""图片生成服务（STEP 9）。

DashScope text2image 走异步：
1. POST /services/aigc/text2image/image-synthesis  (X-DashScope-Async: enable)
   → 返回 task_id
2. GET /tasks/{task_id} 轮询，直到 task_status=SUCCEEDED → results[0].url
3. 下载图片字节，交给上层（worker）落 MinIO

异常统一抛 ImageGenerationError。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from loguru import logger

from app.core.config import settings


class ImageGenerationError(RuntimeError):
    """图片生成失败（统一异常类型）。"""


@dataclass
class GeneratedImage:
    image_bytes: bytes
    image_url: str           # DashScope 临时 URL（24h 失效）
    model_used: str


def generate_image(
    prompt: str,
    *,
    model: str | None = None,
    size: str | None = None,
    n: int = 1,
    negative_prompt: str | None = None,
    poll_interval: float | None = None,
    poll_timeout: int | None = None,
) -> GeneratedImage:
    """同步语义的图片生成：内部异步提交 + 轮询。"""
    if not settings.DASHSCOPE_API_KEY:
        raise ImageGenerationError("DASHSCOPE_API_KEY 未配置")
    if not prompt or not prompt.strip():
        raise ImageGenerationError("prompt 不能为空")

    model_name = model or settings.POSTER_IMAGE_MODEL
    image_size = size or settings.POSTER_IMAGE_SIZE
    interval = poll_interval or settings.POSTER_IMAGE_POLL_INTERVAL
    timeout = poll_timeout or settings.POSTER_IMAGE_POLL_TIMEOUT

    task_id = _submit_task(
        model=model_name,
        prompt=prompt,
        size=image_size,
        n=n,
        negative_prompt=negative_prompt,
    )
    logger.info(f"image task submitted task_id={task_id} model={model_name}")

    image_url = _poll_task(task_id=task_id, interval=interval, timeout=timeout)
    image_bytes = _download(image_url)

    return GeneratedImage(
        image_bytes=image_bytes,
        image_url=image_url,
        model_used=model_name,
    )


def _submit_task(
    *,
    model: str,
    prompt: str,
    size: str,
    n: int,
    negative_prompt: str | None,
) -> str:
    url = f"{settings.DASHSCOPE_IMAGE_BASE_URL}/services/aigc/text2image/image-synthesis"
    payload: dict[str, Any] = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {"size": size, "n": n},
    }
    if negative_prompt:
        payload["input"]["negative_prompt"] = negative_prompt

    resp = _post_json(
        url=url,
        payload=payload,
        extra_headers={"X-DashScope-Async": "enable"},
    )
    output = resp.get("output") or {}
    task_id = output.get("task_id")
    if not task_id:
        raise ImageGenerationError(f"提交失败，无 task_id: {resp}")
    return str(task_id)


def _poll_task(*, task_id: str, interval: float, timeout: int) -> str:
    url = f"{settings.DASHSCOPE_IMAGE_BASE_URL}/tasks/{task_id}"
    deadline = time.time() + timeout

    while time.time() < deadline:
        resp = _get_json(url=url)
        output = resp.get("output") or {}
        status = str(output.get("task_status", "")).upper()

        if status == "SUCCEEDED":
            results = output.get("results") or []
            if not results:
                raise ImageGenerationError(f"task SUCCEEDED 但无 results: {resp}")
            image_url = results[0].get("url")
            if not image_url:
                raise ImageGenerationError(f"results[0] 无 url: {resp}")
            return str(image_url)

        if status in {"FAILED", "CANCELED", "UNKNOWN"}:
            msg = output.get("message") or output.get("code") or status
            raise ImageGenerationError(f"task {status}: {msg}")

        time.sleep(interval)

    raise ImageGenerationError(f"轮询超时（{timeout}s）task_id={task_id}")


def _download(url: str) -> bytes:
    try:
        with request.urlopen(url, timeout=60) as resp:
            return resp.read()
    except Exception as exc:  # noqa: BLE001
        raise ImageGenerationError(f"下载图片失败: {exc}") from exc


def _post_json(
    *,
    url: str,
    payload: dict[str, Any],
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}",
    }
    if extra_headers:
        headers.update(extra_headers)
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise ImageGenerationError(f"HTTP {exc.code}: {body}") from exc
    except Exception as exc:  # noqa: BLE001
        raise ImageGenerationError(f"请求失败: {exc}") from exc


def _get_json(*, url: str) -> dict[str, Any]:
    req = request.Request(
        url=url,
        headers={"Authorization": f"Bearer {settings.DASHSCOPE_API_KEY}"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise ImageGenerationError(f"HTTP {exc.code}: {body}") from exc
    except Exception as exc:  # noqa: BLE001
        raise ImageGenerationError(f"请求失败: {exc}") from exc
