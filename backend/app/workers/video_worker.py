"""视频任务 worker（STEP 10 第一版）。

当前为可运行的阶段化骨架：
pending -> script_done -> images_done -> done
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Any
from urllib import request

from loguru import logger

from app.core.db import SessionLocal
from app.models.generation_log import GenerationLog
from app.models.video_task import VideoTask
from app.services.image_generator import ImageGenerationError, generate_image
from app.services.storage import upload_bytes
from app.services.video_script import generate_video_script
from app.workers.celery_app import celery_app


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _generate_storyboard_images(video_id: str, script_data: dict[str, Any]) -> list[str]:
    shots = script_data.get("shots") if isinstance(script_data, dict) else None
    if not isinstance(shots, list) or not shots:
        raise RuntimeError("script_data.shots 为空，无法生成分镜图")

    urls: list[str] = []
    for idx, shot in enumerate(shots, start=1):
        scene_desc = ""
        if isinstance(shot, dict):
            scene_desc = str(shot.get("scene_desc") or "").strip()
        if not scene_desc:
            scene_desc = f"镜头{idx}，高质量广告风格画面"

        generated = generate_image(prompt=scene_desc, size="1024*576")
        key = f"videos/{video_id}/images/shot_{idx}.png"
        url = upload_bytes(key=key, data=generated.image_bytes, content_type="image/png")
        urls.append(url)
    return urls


def _fake_clip_urls(video_id: str, shot_count: int) -> list[str]:
    return [
        f"https://example.invalid/video/{video_id}/clips/shot_{i + 1}.mp4"
        for i in range(shot_count)
    ]


def _require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg 未安装，无法进行视频片段与拼接")
    return ffmpeg


def _download_to_file(url: str, out_path: str) -> None:
    with request.urlopen(url, timeout=60) as resp:
        data = resp.read()
    with open(out_path, "wb") as f:
        f.write(data)


def _run_cmd(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr = proc.stderr[-1000:] if proc.stderr else ""
        raise RuntimeError(f"命令执行失败: {' '.join(cmd)}\n{stderr}")


def _generate_clips_and_final(
    *,
    video_id: str,
    script_data: dict[str, Any],
    image_urls: list[str],
) -> tuple[list[bytes], bytes]:
    ffmpeg = _require_ffmpeg()

    shots = script_data.get("shots") if isinstance(script_data, dict) else None
    durations: list[int] = []
    if isinstance(shots, list):
        for s in shots:
            if isinstance(s, dict):
                try:
                    durations.append(max(1, int(s.get("duration_sec", 3))))
                except Exception:
                    durations.append(3)
    while len(durations) < len(image_urls):
        durations.append(3)

    clip_bytes_list: list[bytes] = []

    with tempfile.TemporaryDirectory(prefix=f"video_{video_id}_") as tmpdir:
        clip_paths: list[str] = []
        for idx, img_url in enumerate(image_urls, start=1):
            img_path = os.path.join(tmpdir, f"shot_{idx}.png")
            clip_path = os.path.join(tmpdir, f"clip_{idx}.mp4")
            _download_to_file(img_url, img_path)

            duration = durations[idx - 1]
            _run_cmd(
                [
                    ffmpeg,
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    img_path,
                    "-t",
                    str(duration),
                    "-vf",
                    "scale=1280:720,format=yuv420p",
                    "-r",
                    "24",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                    clip_path,
                ]
            )
            clip_paths.append(clip_path)
            with open(clip_path, "rb") as f:
                clip_bytes_list.append(f.read())

        concat_file = os.path.join(tmpdir, "concat.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for p in clip_paths:
                f.write(f"file '{p}'\n")

        final_path = os.path.join(tmpdir, "final.mp4")
        # 先尝试流复制拼接，失败后降级为重编码。
        try:
            _run_cmd(
                [
                    ffmpeg,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    concat_file,
                    "-c",
                    "copy",
                    final_path,
                ]
            )
        except RuntimeError:
            _run_cmd(
                [
                    ffmpeg,
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    concat_file,
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    final_path,
                ]
            )

        with open(final_path, "rb") as f:
            final_bytes = f.read()

    return clip_bytes_list, final_bytes


@celery_app.task(bind=True, name="app.workers.video.generate")
def generate_video_task(
    self,
    video_id_or_payload: str | dict[str, Any],
    action: str = "start",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """视频任务执行。

    兼容历史 `/api/tasks/video-demo`：
    - 若首参是 dict，则按旧占位逻辑返回。
    """
    if isinstance(video_id_or_payload, dict):
        scene_count = int(video_id_or_payload.get("scene_count", 3))
        return {
            "status": "ok",
            "task": "video.generate",
            "scene_count": scene_count,
            "note": "placeholder-demo",
        }

    video_id = video_id_or_payload
    db = SessionLocal()
    try:
        row: VideoTask | None = db.get(VideoTask, video_id)
        if row is None:
            return {"status": "error", "error": f"video {video_id} not found"}

        row.status = "running"
        row.updated_at = _utcnow()
        db.commit()

        if action == "start":
            script_result = generate_video_script(
                prompt=row.prompt,
                shot_count=row.shot_count,
                db=db,
                user_id=row.user_id,
            )
            row.script_data = script_result.script_data
            row.stage = "script_done"
            row.status = "waiting_confirm"
            row.error = None
            row.updated_at = _utcnow()
            db.add(
                GenerationLog(
                    user_id=row.user_id,
                    module="video",
                    model_used=script_result.model_used,
                    prompt_tokens=script_result.prompt_tokens,
                    completion_tokens=script_result.completion_tokens,
                    input_data={"prompt": row.prompt, "shot_count": row.shot_count},
                    output_data={"stage": "script_done", "script": row.script_data},
                )
            )
            db.commit()
            return {"status": "ok", "video_id": video_id, "stage": row.stage}

        if action == "confirm_script":
            if row.stage != "script_done":
                return {
                    "status": "error",
                    "error": f"invalid stage for confirm_script: {row.stage}",
                }
            if payload and isinstance(payload.get("script_data"), dict):
                row.script_data = payload["script_data"]

            try:
                row.image_urls = _generate_storyboard_images(video_id, row.script_data or {})
            except ImageGenerationError as exc:
                row.status = "failed"
                row.error = str(exc)
                row.updated_at = _utcnow()
                db.commit()
                return {"status": "failed", "error": str(exc)}

            row.stage = "images_done"
            row.status = "waiting_confirm"
            row.error = None
            row.updated_at = _utcnow()
            db.add(
                GenerationLog(
                    user_id=row.user_id,
                    module="video",
                    model_used=row.image_model,
                    input_data={"video_id": video_id, "shot_count": row.shot_count},
                    output_data={"stage": "images_done", "image_urls": row.image_urls},
                )
            )
            db.commit()
            return {"status": "ok", "video_id": video_id, "stage": row.stage}

        if action == "confirm_images":
            if row.stage != "images_done":
                return {
                    "status": "error",
                    "error": f"invalid stage for confirm_images: {row.stage}",
                }

            image_urls = row.image_urls or []
            if not isinstance(image_urls, list) or not image_urls:
                return {"status": "error", "error": "image_urls 为空，无法生成视频"}

            clip_blobs, final_blob = _generate_clips_and_final(
                video_id=video_id,
                script_data=row.script_data or {},
                image_urls=image_urls,
            )

            clip_urls: list[str] = []
            for idx, clip_blob in enumerate(clip_blobs, start=1):
                key = f"videos/{video_id}/clips/shot_{idx}.mp4"
                clip_urls.append(
                    upload_bytes(key=key, data=clip_blob, content_type="video/mp4")
                )

            row.clip_urls = clip_urls
            row.final_video_url = upload_bytes(
                key=f"videos/{video_id}/final/final.mp4",
                data=final_blob,
                content_type="video/mp4",
            )
            row.stage = "done"
            row.status = "done"
            row.error = None
            row.updated_at = _utcnow()
            db.add(
                GenerationLog(
                    user_id=row.user_id,
                    module="video",
                    model_used=row.clip_model,
                    input_data={"video_id": video_id, "shot_count": row.shot_count},
                    output_data={"stage": "done", "final_video": row.final_video_url},
                )
            )
            db.commit()
            return {
                "status": "ok",
                "video_id": video_id,
                "stage": row.stage,
                "final_video_url": row.final_video_url,
            }

        return {"status": "error", "error": f"unknown action: {action}"}
    except Exception as exc:  # noqa: BLE001
        logger.error(f"video task failed: id={video_id} action={action} err={exc}")
        row = db.get(VideoTask, video_id)
        if row is not None:
            row.status = "failed"
            row.error = str(exc)
            row.updated_at = _utcnow()
            db.commit()
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()
