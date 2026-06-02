# Backend

FastAPI + Celery + SQLAlchemy。详细架构与修改入口见根目录 [`AI_GUIDE.md`](../AI_GUIDE.md)。

## 启动

```bash
cd backend
uv sync                                       # 装/同步依赖
uv run uvicorn app.main:app --reload --port 8000
```

- 首页：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 前置条件

基础设施容器已启动（在项目根目录跑 `docker compose up -d`），见 [`../docs/infra.md`](../docs/infra.md)。

## 目录速览

```
backend/
├── pyproject.toml
└── app/
    ├── main.py            FastAPI 入口
    └── core/
        └── config.py      读取 .env 的配置中心
```
