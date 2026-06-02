# Backend

FastAPI + Celery + SQLAlchemy。详细架构与修改入口见根目录 [`AI_GUIDE.md`](../AI_GUIDE.md)。

## 启动

```bash
cd backend
uv sync                                       # 装/同步依赖
uv run uvicorn app.main:app --reload --port 8000
```

另开一个终端启动 Celery Worker：

```bash
cd backend
uv run celery -A app.workers.celery_app:celery_app worker -l info
```

运行自动化测试：

```bash
cd backend
uv run pytest -q
```

- 首页：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 异步任务投递：POST http://localhost:8000/api/tasks/ping
- 任务状态查询：GET  http://localhost:8000/api/tasks/{task_id}

## 前置条件

基础设施容器已启动（在项目根目录跑 `docker compose up -d`），见 [`../docs/infra.md`](../docs/infra.md)。

## 目录速览

```
backend/
├── pyproject.toml
└── app/
    ├── main.py            FastAPI 入口
    ├── core/
    │   └── config.py      读取 .env 的配置中心
    ├── api/
    │   ├── auth.py        登录注册 API
    │   └── tasks.py       异步任务 API（STEP 5）
    └── workers/
        ├── celery_app.py  Celery 应用入口
        ├── poster_worker.py
        └── video_worker.py
```
