"""海报生成 Celery 任务（STEP 9）。

入参 poster_id 与 PosterTask 主键一致（也用作 celery task_id）。
流程：
  1) 读 PosterTask 行，标记 running
  2) image_generator.generate_image(prompt)
  3) storage.upload_bytes(...) → public URL
  4) 写回 image_url + status=done；失败写 error + status=failed
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from loguru import logger

from app.core.db import SessionLocal
from app.models.generation_log import GenerationLog
from app.models.poster_task import PosterTask
from app.services.image_generator import ImageGenerationError, generate_image
from app.services.storage import upload_bytes
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="app.workers.poster.generate")
def generate_poster_task(self, poster_id: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        row: PosterTask | None = db.get(PosterTask, poster_id)
        if row is None:
            return {"status": "error", "error": f"poster {poster_id} not found"}

        row.status = "running"
        row.updated_at = datetime.now(timezone.utc)
        db.commit()

        try:
            generated = generate_image(prompt=row.prompt, size=row.size)
        except ImageGenerationError as exc:
            logger.error(f"poster {poster_id} image gen failed: {exc}")
            row.status = "failed"
            row.error = str(exc)
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "failed", "error": str(exc)}

        key = f"posters/{poster_id}.png"
        try:
            url = upload_bytes(
                key=key, data=generated.image_bytes, content_type="image/png"
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"poster {poster_id} upload failed: {exc}")
            row.status = "failed"
            row.error = f"upload failed: {exc}"
            row.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {"status": "failed", "error": str(exc)}

        row.image_url = url
        row.status = "done"
        row.updated_at = datetime.now(timezone.utc)

        db.add(
            GenerationLog(
                user_id=row.user_id,
                module="poster",
                model_used=generated.model_used,
                input_data={"prompt": row.prompt, "size": row.size},
                output_data={"image_url": url},
            )
        )
        db.commit()

        return {
            "status": "done",
            "image_url": url,
            "model": generated.model_used,
        }
    finally:
        db.close()
