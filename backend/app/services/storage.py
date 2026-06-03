"""MinIO 对象存储封装。

提供：
- ensure_bucket(): 启动期幂等地创建 bucket
- upload_bytes(key, data, content_type) -> public_url
- public_url(key) -> 浏览器可访问的 URL
"""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO

from loguru import logger
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


@lru_cache(maxsize=1)
def get_minio_client() -> Minio:
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def ensure_bucket() -> None:
    client = get_minio_client()
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)
        logger.info(f"MinIO bucket created: {settings.MINIO_BUCKET}")


def public_url(key: str) -> str:
    base = settings.MINIO_PUBLIC_BASE_URL
    if not base:
        scheme = "https" if settings.MINIO_SECURE else "http"
        base = f"{scheme}://{settings.MINIO_ENDPOINT}"
    return f"{base.rstrip('/')}/{settings.MINIO_BUCKET}/{key.lstrip('/')}"


def upload_bytes(key: str, data: bytes, content_type: str = "image/png") -> str:
    """上传字节到 MinIO，返回 public URL。"""
    client = get_minio_client()
    try:
        ensure_bucket()
        client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=key,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
    except S3Error as exc:
        raise RuntimeError(f"MinIO 上传失败: {exc}") from exc
    return public_url(key)
