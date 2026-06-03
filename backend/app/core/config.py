"""集中式配置：所有环境变量从这里读，业务代码不再用 os.getenv。

新增配置项时，记得同步更新 ../../.env.example 和 AI_GUIDE.md 第 7 节。
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（backend/ 的上一层）
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # ---- 模型 API Key ----
    DASHSCOPE_API_KEY: str = ""

    # ---- 文案 & 策划（两步流程）----
    COPY_DRAFT_MODEL: str = "deepseek-v4"          # 初稿：DeepSeek-V4
    COPY_POLISH_MODEL: str = "qwen-plus"            # 润色：Qwen3.7-Max

    # ---- 海报图片生成 ----
    POSTER_IMAGE_MODEL: str = "qwen-image-2.0"     # 海报底图

    # ---- 视频生成 ----
    VIDEO_DEEPSEEK_MODEL: str = "deepseek-v4"       # 脚本生成
    VIDEO_IMAGE_MODEL: str = "qwen-image-2.0"      # 分镜图
    VIDEO_CLIP_MODEL: str = "wan2.7-14b-text2video" # 视频片段

    # ---- 数据库 ----
    DATABASE_URL: str = (
        "postgresql+psycopg://aigc:aigc_dev_pass@localhost:5432/aigc"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_DEFAULT_QUEUE: str = "aigc_default"
    CELERY_TASK_TRACK_STARTED: bool = True
    QDRANT_URL: str = "http://localhost:6333"

    # ---- 对象存储 ----
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "aigc"
    MINIO_SECURE: bool = False                       # True 走 https
    MINIO_PUBLIC_BASE_URL: str | None = None         # 浏览器可访问的 base，默认推断 http(s)://{endpoint}

    # ---- 图片生成 ----
    DASHSCOPE_IMAGE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"
    POSTER_IMAGE_SIZE: str = "1024*1024"
    POSTER_IMAGE_POLL_INTERVAL: float = 3.0          # 秒
    POSTER_IMAGE_POLL_TIMEOUT: int = 180             # 秒

    # ---- 安全 ----
    JWT_SECRET: str = "please-change-me"
    JWT_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
