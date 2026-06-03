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

当前落地优先测试（推荐先执行）：

文案验收样例（固定输入与验收标准）：`../docs/copy_acceptance_cases.md`

```bash
cd backend
uv run pytest -q tests/test_copywriter.py tests/test_reviews.py tests/test_poster.py
```

- 首页：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 文案生成：POST http://localhost:8000/api/copy/generate
- 批量好评：POST http://localhost:8000/api/reviews/generate
- 规则审核：POST http://localhost:8000/api/compliance/check
- 异步任务投递：POST http://localhost:8000/api/tasks/ping
- 任务状态查询：GET  http://localhost:8000/api/tasks/{task_id}
- 海报生成：POST http://localhost:8000/api/poster/generate
- 海报查询：GET  http://localhost:8000/api/poster/{poster_id}
- 视频启动：POST http://localhost:8000/api/video/start
- 视频查询：GET  http://localhost:8000/api/video/{video_id}
- 视频确认：POST http://localhost:8000/api/video/confirm

当前优先交付能力：文案策划、批量好评、海报生成。
视频链路保留可运行，后续按需求继续增强。

视频阶段流转：
- `start`：LLM 生成脚本（含检索上下文注入）
- `confirm(script_done)`：逐镜头文生图并上传 MinIO
- `confirm(images_done)`：ffmpeg 生成片段并拼接最终 MP4

## 前置条件

基础设施容器已启动（在项目根目录跑 `docker compose up -d`），见 [`../docs/infra.md`](../docs/infra.md)。

视频合成需要系统安装 `ffmpeg`（STEP 11 第一版）。

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
    │   ├── copywriter.py  广告文案 API（STEP 7）
    │   ├── reviews.py     批量好评 API（STEP 8）
    │   ├── poster.py      海报 API（STEP 9）
    │   ├── video.py       视频 API（STEP 10）
    │   ├── compliance.py  规则审核 API（STEP 6）
    │   └── tasks.py       异步任务 API（STEP 5）
    ├── models/
    │   ├── poster_task.py
    │   └── video_task.py
    ├── schemas/
    │   ├── poster.py
    │   └── video.py
    ├── services/
    │   ├── llm_router.py
    │   ├── copywriter.py
    │   ├── review_generator.py
    │   ├── image_generator.py
    │   ├── video_script.py
    │   ├── rag_retriever.py
    │   ├── storage.py
    │   └── compliance/
    ├── prompts/
    │   ├── copywriter/
    │   └── reviews/
    └── workers/
        ├── celery_app.py  Celery 应用入口
        ├── poster_worker.py
        └── video_worker.py
```
