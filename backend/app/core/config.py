"""集中式配置：所有环境变量从这里读，业务代码不再用 os.getenv。

新增配置项时，记得同步更新 ../../.env.example 和 AI_GUIDE.md 第 7 节。
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（backend/ 的上一层）
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # ---- 模型路由 ----
    LLM_PROVIDER: str = "github"
    GITHUB_TOKEN: str = ""
    GITHUB_MODELS_ENDPOINT: str = "https://models.inference.ai.azure.com"
    GITHUB_MODELS_NAME: str = "gpt-4o-mini"
    DASHSCOPE_API_KEY: str = ""

    # ---- 数据库 ----
    DATABASE_URL: str = (
        "postgresql+psycopg://aigc:aigc_dev_pass@localhost:5432/aigc"
    )
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"

    # ---- 对象存储 ----
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "aigc"

    # ---- 安全 ----
    JWT_SECRET: str = "please-change-me"
    JWT_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
