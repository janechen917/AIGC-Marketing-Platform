# AI 接手指南（AI_GUIDE）

> 本文件是给 **AI 助手 / 新加入的开发者** 的导航手册。
> 任何代码修改前，先读这份文档，可以避免大量探索性搜索。
> **修改完代码后，请同步更新本文件（尤其是第 4 节）。**

---

## 1. 系统总览

**项目**：AIGC 营销内容生成平台（个人/小团队版，本地开发优先）

**一句话**：把多个大模型（文案 / 图片 / 视频 / TTS）串成一条流水线，加上品牌知识库（RAG）和规则审核，让小团队快速产出广告文案、好评文案、海报、短视频。

**当前阶段**：STEP 11 第一版完成（技术状态）；当前执行优先级切换为“文案策划 + 批量好评 + AIGC 图片先落地”。

### 目标架构（最终态）

```
[Next.js 前端] ──► [FastAPI API] ──► [Postgres + Redis + Qdrant + MinIO]
                        │
                        ├─► [Celery Worker] ──► [模型路由层]
                        │                          ├─ DeepSeek-V4（文案/策划初稿 + 视频脚本）
                        │                          ├─ Qwen3.7-Max（文案/策划润色）
                        │                          ├─ Qwen-Image-2.0 / Qwen-VL（DashScope）
                        │                          ├─ Edge-TTS / CosyVoice
                        │                          └─ Wan2.7-Video（视频片段）
                        └─► [内容安全 API]
```

**核心原则**：
- 所有模型走 API，不本地推理（CPU 即可开发）
- 所有"图/视频生成"必须走 Celery 异步任务
- 所有"换模型"只改环境变量，业务代码不动（靠 `llm_router.py`）

---

## 2. 目录结构地图

> 说明：标 `[未建]` 的目录会在后续 STEP 创建，本表会随之更新。

```
AIGC-Marketing-Platform/
├── AI_GUIDE.md              ← 本文件（AI 必读）
├── AI_GUIDE_INDEX.md        ← 极简入口
├── README.md                ← 人类使用说明
├── .env.example             ← 环境变量模板
├── .gitignore
├── docker-compose.yml       ← 4 个基础设施容器（postgres/redis/qdrant/minio）
├── docker-data/      [运行时] 容器数据持久化目录（被 gitignore）
├── docs/
│   ├── plan.md              ← 完整产品方案（v3）
│   └── infra.md             ← 基础设施运维速查
├── frontend/                 ← Next.js 14 + TypeScript + TailwindCSS（前端 STEP 10 第一版已建）
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── .env.local.example    ← NEXT_PUBLIC_API_BASE=http://localhost:8000
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx          ← 跳转到 /login
│   │   ├── globals.css
│   │   ├── (auth)/login/page.tsx
│   │   └── (dashboard)/
│   │       ├── layout.tsx          顶部导航 + 退出
│   │       ├── dashboard/page.tsx  概览（/api/auth/me + /health）
│   │       ├── copy/page.tsx       广告文案表单（POST /api/copy/generate）
│   │       ├── reviews/page.tsx    批量好评 + CSV 导出（POST /api/reviews/generate）
│   │       ├── poster/page.tsx     海报生成 + 轮询（POST /api/poster/generate）
│   │       ├── video/page.tsx      视频任务启动/确认/轮询（/api/video/*）
│   │       └── tasks/page.tsx      Celery 任务投递 + 轮询（/api/tasks/*）
│   └── lib/
│       ├── api.ts            ← fetch 封装（自动带 JWT）
│       ├── auth.ts           ← localStorage token 读写
│       ├── useRequireAuth.ts ← 未登录则跳 /login
│       ├── compliance.tsx    ← 合规状态徽章 + issue 列表
│       └── types.ts          ← 与后端 schema 对齐的 TS 类型
└── backend/                  ← FastAPI 后端（STEP 10 第一版）
    ├── pyproject.toml        ← 依赖声明（uv 管理）
    ├── .python-version       ← 锁定 3.12
    ├── README.md             ← 后端启动速查
    ├── .venv/         [运行时] uv 创建的虚拟环境
    └── app/
        ├── main.py           ← FastAPI 入口 + /health
        ├── core/
        │   ├── config.py     ← 读 .env 的配置中心
        │   ├── db.py         ← SQLAlchemy engine + SessionLocal
        │   └── security.py   ← JWT + 密码 hash/verify
        ├── api/
        │   ├── auth.py       ← 注册 / 登录 / 当前用户
        │   ├── compliance.py ← 规则审核 API（/api/compliance/check）
        │   ├── copywriter.py ← 广告文案 API（/api/copy/generate）
        │   ├── poster.py     ← 海报 API（POST /api/poster/generate / GET /api/poster/{id}）
        │   ├── reviews.py    ← 批量好评 API（/api/reviews/generate）
        │   ├── video.py      ← 视频 API（start / get / confirm）
        │   └── tasks.py      ← 异步任务 API（ping / video-demo / 状态查询）
        ├── models/           ← User / GenerationLog / UsageLog / PosterTask / VideoTask
        ├── schemas/
        │   ├── poster.py     ← STEP 9：海报请求 / 响应 schema
        │   └── video.py      ← STEP 10：视频请求 / 响应 schema
        ├── services/
        │   ├── llm_router.py ← STEP 4：统一模型调用入口（DashScope）
        │   ├── copywriter.py ← STEP 7：文案生成（初稿+润色+审核）
        │   ├── review_generator.py ← STEP 8：批量好评（人设池+去重）
        │   ├── image_generator.py  ← STEP 9/10：DashScope 文生图（异步 + 轮询）
        │   ├── video_script.py     ← STEP 10.1：视频脚本生成（LLM + RAG context）
        │   ├── rag_retriever.py    ← STEP 11：轻量检索注入（后续可换 Qdrant）
        │   ├── storage.py          ← STEP 9：MinIO 上传 + public URL
        │   └── compliance/
        │       ├── engine.py
        │       ├── sensitive.py
        │       ├── ad_law.py
        │       ├── brand.py
        │       ├── format.py
        │       └── wordlists/sensitive.txt
        └── workers/
            ├── celery_app.py  ← STEP 5：Celery 应用入口
            ├── poster_worker.py
            └── video_worker.py
    └── prompts/
        ├── copywriter/
        │   ├── draft.md
        │   └── polish.md
        └── reviews/
            └── generate.md
```

**后续 STEP 完成后会变成**（提前展示，便于理解）：

```
backend/
├── pyproject.toml
├── alembic/                       数据库迁移
└── app/
    ├── main.py                    FastAPI 入口
    ├── core/
    │   ├── config.py              读取 .env
    │   ├── security.py            JWT 加解密
    │   └── db.py                  数据库连接
    ├── api/
    │   ├── auth.py                登录注册
    │   ├── copywriter.py          广告文案 API
    │   ├── reviews.py             批量好评 API
    │   ├── poster.py              海报 API
    │   └── video.py               视频 API
    ├── services/
    │   ├── llm_router.py         ⭐ 统一模型调用入口
    │   ├── copywriter.py          文案业务逻辑
    │   ├── review_generator.py    好评生成 + 防雷同
    │   ├── poster_composer.py     海报模板合成
    │   └── compliance/            规则审核引擎
    │       ├── sensitive.py       敏感词
    │       ├── ad_law.py          《广告法》违禁词
    │       ├── brand.py           品牌合规
    │       └── format.py          格式校验
    ├── workers/
    │   ├── celery_app.py          Celery 入口
    │   ├── poster_worker.py
    │   └── video_worker.py        FFmpeg 6 步流水线
    ├── models/                    SQLAlchemy ORM
    │   ├── user.py
    │   ├── generation_log.py
    │   └── usage_log.py
    ├── prompts/                   Prompt 模板（P2 移到 DB）
    │   ├── copywriter/
    │   └── reviews/
    └── rag/                       (P2)
        ├── ingest.py
        └── retriever.py

frontend/
└── app/
    ├── (auth)/login/
    └── (dashboard)/
        ├── copy/                  广告文案页
        ├── reviews/               批量好评页
        ├── poster/                Polotno 画布
        ├── video/                 视频生成 + 进度
        └── kb/                    知识库管理
```

---

## 3. 核心概念词典

| 术语 | 含义 |
|---|---|
| **模型路由层** | `services/llm_router.py`。所有 LLM 调用必须经过它，统一封装：选模型 / 缓存 / 重试 / 成本统计。改模型优先通过 `.env` 中各模块模型变量完成。 |
| **Celery 任务** | 跑在独立 Worker 进程的后台任务。图片/视频生成耗时长，必须异步。前端通过 `task_id` 轮询进度。 |
| **规则审核** | 4 类：敏感词（DFA）/ 广告法违禁词 / 品牌合规（正则）/ 格式校验。所有 LLM 输出前必须过审。 |
| **RAG** | Retrieval-Augmented Generation。上传品牌手册 → BGE-M3 向量化 → Qdrant 存储 → 生成时检索注入。 |
| **Prompt 模板中心** | DB 表 `prompt_templates`，存模板 + 版本号。P1 先用 `app/prompts/` 文件，P2 迁到 DB。 |
| **Polotno** | 前端可编辑画布 SDK（类 Canva）。海报生成后用它做"可拖拽/可改字"的编辑器。 |
| **GitHub Models** | https://models.inference.ai.azure.com 提供的免费 LLM API（gpt-4o-mini 等）。用 GitHub PAT 鉴权，有速率限制。P1 默认用它。 |

---

## 4. 常见修改场景定位表 ⭐（最重要）

> 这是本文件最有价值的部分。**未来添加新场景时请补充这张表。**

| 想做什么 | 改哪里 | 备注 |
|---|---|---|
| 换文案初稿模型 | `.env` 的 `COPY_DRAFT_MODEL` 字段 | 默认 `deepseek-v4` |
| 换文案润色模型 | `.env` 的 `COPY_POLISH_MODEL` 字段 | 默认 `qwen-plus`（Qwen3.7-Max） |
| 新增一个 LLM 厂商 | `backend/app/services/llm_router.py` 加分支 | 实现 `chat(messages)` 接口 |
| 加一个新的目标平台（如抖音文案） | `services/copywriter.py` 的 `PLATFORMS` 常量 + `frontend/app/(dashboard)/copy/page.tsx` 下拉项 | — |
| 改广告文案初稿 Prompt | `backend/app/prompts/copywriter/draft.md` | 控制 DeepSeek-V4 框架结构 |
| 改广告文案润色 Prompt | `backend/app/prompts/copywriter/polish.md` | 控制 Qwen3.7-Max 风格表达 |
| 改海报图片生成模型 | `.env` 的 `POSTER_IMAGE_MODEL` 字段 | 默认 `qwen-image-2.0` |
| 调整文本模型重试/超时策略 | `backend/app/services/llm_router.py` | `max_retries` / `default_timeout` |
| 改 Celery Broker / Backend | `.env` 的 `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | 默认走 Redis |
| 新增异步任务 | `backend/app/workers/*.py` + `backend/app/api/tasks.py` | Worker 定义 + API 投递/查询 |
| 增加/修改后端自动化测试 | `backend/tests/` | 运行 `uv run pytest -q` |
| 修改 GitHub CI 流水线 | `.github/workflows/ci.yml` | push/PR 自动跑后端测试 |
| 改前端 API 基地址 | `frontend/.env.local` 的 `NEXT_PUBLIC_API_BASE` | 默认 `http://localhost:8000` |
| 改前端 fetch 封装 / 鉴权头 | `frontend/lib/api.ts` + `frontend/lib/auth.ts` | localStorage 存 JWT |
| 加新的前端顶部导航项 | `frontend/app/(dashboard)/layout.tsx` 的 `NAV` 常量 | — |
| 改前端与后端对齐的 TS 类型 | `frontend/lib/types.ts` | 与 `backend/app/schemas/*` 保持一致 |
| 改任务轮询频率 | `frontend/app/(dashboard)/tasks/page.tsx` 的 `setInterval(poll, 1500)` | 默认 1.5s |
| 加 / 改敏感词 | `backend/app/services/compliance/wordlists/*.txt` | 进程启动时加载 |
| 加广告法违禁词 | `backend/app/services/compliance/ad_law.py` 中的列表 | — |
| 改批量好评的"人设池" | `backend/app/services/review_generator.py` 的 `PERSONAS` | — |
| 改批量好评的去重阈值 | 同上文件的 `SIMILARITY_THRESHOLD` | 默认 0.85 |
| 加新的海报模板 | `backend/app/services/poster_composer.py` + `backend/templates/poster/*.json` | — |
| 改视频脚本 Prompt | `backend/app/prompts/video/script.md` | 控制 DeepSeek-V4 脚本格式 |
| 改分镜图生成参数 | `backend/app/workers/video_worker.py` 的 `gen_images()` | 模型由 `VIDEO_IMAGE_MODEL` 控制，默认 Qwen-Image-2.0 |
| 改视频片段生成参数 | `backend/app/workers/video_worker.py` 的 `gen_clips()` | Wan2.7-Video 时长/运动幅度等 |
| 重新生成单张分镜图 | POST `/api/video/retry-image` | 传 `task_id` + `shot_index` |
| 重新生成单个视频片段 | POST `/api/video/retry-clip` | 传 `task_id` + `shot_index` |
| 启动视频任务 | POST `/api/video/start` | 传 `prompt` + `shot_count` |
| 查询视频任务 | GET `/api/video/{video_id}` | 返回 stage/status/script/images/clips |
| 确认某步进入下一阶段 | POST `/api/video/confirm` | 传 `video_id` + `stage` + 修改后的 `payload` |
| 加新的数据表 | `backend/app/models/` 加 ORM + `alembic revision --autogenerate` | — |
| 加新的前端页面 | `frontend/app/(dashboard)/<name>/page.tsx` | 自动出现在路由 |
| 加环境变量 | `.env.example` + `backend/app/core/config.py` | 两处都要改 |
| 排查 LLM 调用失败 | 看 `backend/app/services/llm_router.py` 的日志 + `generation_logs` 表 | — |
| 改基础设施容器 / 端口 | `docker-compose.yml` + 同步 `.env` 连接串 | 详见 `docs/infra.md` |
| 重置全部本地数据 | `docker compose down && rm -rf docker-data/` | 不可恢复 |

---

## 5. 数据流时序图

### 5.1 广告文案生成（同步请求）

```
用户填表 → 前端 POST /api/copy/generate
            ↓
        api/copywriter.py  (校验入参)
            ↓
        services/copywriter.py
            ├─ rag.retriever.query(品牌上下文)                    [P2 起]
            ├─ services/llm_router.chat(draft_prompt,             ← DeepSeek-V4 生成初版框架
            │                          model=COPY_DRAFT_MODEL)
            ├─ services/llm_router.chat(polish_prompt+draft,      ← Qwen3.7-Max 润色优化
            │                          model=COPY_POLISH_MODEL)
            └─ services/compliance.check_all(polished_text)
            ↓
        写入 generation_logs
            ↓
        返回 JSON
```

### 5.2 海报生成（异步任务）

```
前端 POST /api/poster/generate → 立即返回 task_id
                                    ↓
                            Celery: poster_worker
                                ├─ Qwen-VL 提取产品图特征
                                ├─ LLM 生成 image_prompt
                                ├─ Qwen-Image-2.0 生成底图
                                └─ Pillow 合成（底图+产品+Logo+文字）
                                    ↓
                            存 MinIO + 更新 task 状态
                                    ↓
前端轮询 GET /api/poster/status/{task_id} → 拿到图 URL
                                    ↓
                            Polotno 画布加载图层，可编辑
```

### 5.3 AI 视频生成（3 步交互式，每步手动确认）

```
前端 POST /api/video/start → 立即返回 video_id，stage="pending"
                                    ↓
                        ━━━ STEP 1: 脚本生成 ━━━
                        Celery: video_worker(start)
                            └─ DeepSeek-V4 生成脚本 JSON（含 RAG 检索上下文注入）
                               (含 narration + 每镜头 scene_desc)
                                    ↓
                        更新 video_tasks.stage = "script_done"
                        存脚本 JSON 到 Postgres
                                    ↓
前端轮询到 script_done → 显示脚本编辑卡片（可修改每个 scene_desc）
用户确认 → 前端 POST /api/video/confirm { video_id, stage: "script_done", payload: {...} }
                                    ↓
                        ━━━ STEP 2: 分镜图生成 ━━━
                        Celery: video_worker(confirm_script)
                            └─ Qwen-Image-2.0 逐镜头生成图片 + 上传 MinIO
                                    ↓
                        更新 stage = "images_done"
                        存图片 URL 列表到 Postgres + MinIO
                                    ↓
前端轮询到 images_done → 网格展示所有分镜图（可单张重新生成）
用户确认 → 前端 POST /api/video/confirm { video_id, stage: "images_done", payload: {...} }
                                    ↓
                        ━━━ STEP 3: 视频片段生成与合成 ━━━
                        Celery: video_worker(confirm_images)
                            ├─ ffmpeg 按分镜图逐镜头生成 MP4 片段
                            └─ ffmpeg concat 合并为最终 MP4
                                    ↓
                        更新 stage = "done"，存最终 MP4 到 MinIO
                                    ↓
前端轮询到 done → 显示最终视频预览 + 下载链接
```

`video_tasks.stage` 枚举：`pending` → `script_done` → `images_done` → `done` | `failed`

---

## 6. 数据库 Schema 速查

> 核心表已建，含 STEP 9/10 新增任务表。

| 表名 | 主要字段 | 说明 |
|---|---|---|
| `users` | `id`, `email`(unique), `hashed_password`, `role`(admin/user), `is_active`, `created_at` | JWT 用户体系 |
| `generation_logs` | `id`, `user_id`(FK), `module`, `prompt`, `result`, `model`, `latency_ms`, `created_at` | 所有生成记录 |
| `usage_logs` | `id`, `user_id`(FK), `module`, `model`, `tokens_in`, `tokens_out`, `cost_usd`, `created_at` | 成本统计 |
| `poster_tasks` | `id`, `user_id`, `prompt`, `status`, `image_url`, `error`, `created_at` | 海报异步任务 |
| `video_tasks` | `id`, `user_id`, `prompt`, `stage`, `status`, `script_data`, `image_urls`, `clip_urls`, `final_video_url` | 视频多阶段任务 |

后续待建：`prompt_templates` / `kb_documents`

**Alembic 常用命令**：
```bash
cd backend
uv run alembic revision --autogenerate -m "<描述>"  # 生成迁移文件
uv run alembic upgrade head                          # 应用迁移
uv run alembic downgrade -1                          # 回滚一步
uv run alembic current                               # 查看当前版本
```

---

## 7. 环境变量清单

详见 `.env.example`。关键变量：

| 变量 | 作用 | 默认值 |
|---|---|---|
| `DASHSCOPE_API_KEY` | DeepSeek-V4 / Qwen3.7-Max / Qwen-Image-2.0 / Qwen-VL / Wan2.7-Video（均走 DashScope） | — |
| `COPY_DRAFT_MODEL` | 文案/策划初稿模型名 | `deepseek-v4` |
| `COPY_POLISH_MODEL` | 文案/策划润色模型名 | `qwen-plus`（Qwen3.7-Max 接口名） |
| `POSTER_IMAGE_MODEL` | 海报图片生成模型名 | `qwen-image-2.0` |
| `VIDEO_DEEPSEEK_MODEL` | 脚本生成模型名 | `deepseek-v4` |
| `VIDEO_IMAGE_MODEL` | 分镜图生成模型名 | `qwen-image-2.0` |
| `VIDEO_CLIP_MODEL` | 视频片段生成模型名 | `wan2.7-14b-text2video` |
| `DATABASE_URL` | Postgres 连接串 | `postgresql+psycopg://...` |
| `REDIS_URL` | Celery + 缓存 | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker 地址 | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery 结果存储地址 | `redis://localhost:6379/1` |
| `CELERY_TASK_DEFAULT_QUEUE` | Celery 默认队列名 | `aigc_default` |
| `CELERY_TASK_TRACK_STARTED` | 是否追踪 STARTED 状态 | `true` |
| `JWT_SECRET` | 登录令牌签名 | — |

---

## 8. 启动 / 调试 / 排错速查

### 基础设施（STEP 1 已完成）

```bash
docker compose up -d            # 启动 postgres + redis + qdrant + minio
docker compose ps               # 查看 4 个容器状态
docker compose logs -f postgres # 跟日志
docker compose down             # 停止（数据保留在 docker-data/）
```

连通性快速验证：

```bash
docker compose exec redis redis-cli ping       # PONG
docker compose exec postgres psql -U aigc -d aigc -c '\l'
curl http://localhost:6333/collections          # Qdrant
# 浏览器: http://localhost:9001  (MinIO 控制台, minioadmin/minioadmin)
```

完整运维手册见 [`docs/infra.md`](docs/infra.md)。

### 后端 / 前端启动

**后端（STEP 8 已完成）**：

```bash
cd backend
uv sync                                        # 首次装依赖
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

- 首页: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health  → `{api/postgres/redis: ok}`
- 注册: POST http://localhost:8000/api/auth/register
- 登录: POST http://localhost:8000/api/auth/login  → 返回 JWT token
- 当前用户: GET http://localhost:8000/api/auth/me  （Bearer token）
- 文案生成: POST http://localhost:8000/api/copy/generate
- 批量好评: POST http://localhost:8000/api/reviews/generate
- 规则审核: POST http://localhost:8000/api/compliance/check
- 异步连通性任务: POST http://localhost:8000/api/tasks/ping
- 任务状态查询: GET  http://localhost:8000/api/tasks/{task_id}
- 海报生成: POST http://localhost:8000/api/poster/generate  (异步)
- 海报查询: GET  http://localhost:8000/api/poster/{poster_id}
- 视频启动: POST http://localhost:8000/api/video/start
- 视频查询: GET  http://localhost:8000/api/video/{video_id}
- 视频确认: POST http://localhost:8000/api/video/confirm

**前端（前端 STEP 10 第一版已完成）**：

```bash
cd frontend
cp .env.local.example .env.local   # 调整 NEXT_PUBLIC_API_BASE
npm install
npm run dev
```

- 首页（自动跳 /login）: http://localhost:3000
- 登录页: http://localhost:3000/login
- 概览页: http://localhost:3000/dashboard
- 广告文案: http://localhost:3000/copy
- 批量好评: http://localhost:3000/reviews
- 海报生成: http://localhost:3000/poster
- 视频生成: http://localhost:3000/video
- 任务控制台: http://localhost:3000/tasks

> 登录前请先用后端 `POST /api/auth/register` 创建账号。
> 视频当前为 STEP 11 第一版，后续将升级为向量检索 + Wan 片段 + 音频字幕全链路。

---

## 9. 已知限制与 TODO

- 当前处于 **STEP 11 第一版完成**：
- 视频脚本：真实 LLM 生成（含检索上下文注入）
- 分镜图：真实文生图 + MinIO 上传
- 视频合成：FFmpeg 逐镜头片段 + concat 最终 MP4
- 仍待增强：Qdrant 向量检索、视频片段模型（如 Wan）与音频/字幕细化
- 视频生成 MVP 暂未支持人物口型对齐
- 多语言：当前只考虑中文 + 英文
- 不做企业级特性：多租户 / SSO / 审批流 / 计费

### 9.1 当前优先执行序列（落地优先）

1. 文案策划（`/api/copy/generate` + `/copy`）
2. 批量好评（`/api/reviews/generate` + `/reviews`）
3. AIGC 图片（`/api/poster/generate` + `/poster`）
4. 视频链路维持可运行，不作为当前交付阻塞项

### 9.2 当前测试目标（可直接执行）

文案验收样例（固定输入与检查口径）：

- `docs/copy_acceptance_cases.md`

批量好评验收样例（固定输入与检查口径）：

- `docs/reviews_acceptance_cases.md`

后端聚焦测试：

```bash
cd backend
uv run pytest -q tests/test_copywriter.py tests/test_reviews.py tests/test_poster.py
```

前端构建校验：

```bash
cd frontend
npm run build
```

### 9.3 完整项目收尾目标（下一阶段执行清单）

1. **STEP 12（RAG 正式化）**
    - 文档上传/解析/切片/Embedding 入库
    - Qdrant 检索替换当前轻量检索
    - 检索结果重排与品牌知识注入策略
2. **STEP 13（视频模型升级）**
    - 接入 Wan 视频片段生成（逐镜头）
    - 保留 ffmpeg 兜底与失败回退
    - 片段级重试与幂等
3. **STEP 14（成片增强）**
    - TTS 旁白 + 字幕（SRT/ASS）
    - BGM/转场/封面与导出规格
    - 视频质量校验（时长/黑帧/无音轨）
4. **STEP 15（交付与稳定性）**
    - 完整回归测试（后端/前端/端到端）
    - 成本统计与告警监控
    - 文档、部署脚本与验收用例收尾

---

## 10. 开发节奏（当前位置 = STEP 11 第一版完成）

```
[✓] STEP 0  脚手架与导航文件
[✓] STEP 1  Docker 基础设施（postgres/redis/qdrant/minio）
[✓] STEP 2  后端骨架（FastAPI hello）
[✓] STEP 3  数据库 + JWT 用户体系
[✓] STEP 4  模型路由层（接 DashScope：DeepSeek-V4 / Qwen3.7-Max）
[✓] STEP 5  Celery 异步任务框架
[✓] STEP 6  规则审核引擎
[✓] STEP 7  广告文案生成（第一个完整功能）
[✓] STEP 8  批量好评生成
─── P1 后端完成 ───
[✓] 前端 STEP 1  Next.js 骨架 + 登录 + 概览页
[✓] 前端 STEP 2  文案 / 好评 / 任务页（接已就绪的后端 API）
[✓] STEP 9   海报：DashScope 文生图 + MinIO + 前端 /poster 页
[✓] STEP 10  视频：video_tasks + /api/video + 前端 /video（骨架版）
[✓] STEP 11  视频：脚本/分镜真实生成 + FFmpeg 合成 + 检索注入（第一版）
[ ] L1   文案策划交付收敛（稳定性/提示词/错误处理/验收样例）
[ ] L2   批量好评交付收敛（去重质量/CSV体验/参数边界）
[ ] L3   AIGC 图片交付收敛（出图成功率/任务可观测/失败重试）
[ ] L4   视频后续增强（按需求再推进）
```

完成每个 STEP 后，请在此处打勾，并更新第 2、4、6、7、8 节相关内容。
