# AI 接手指南（AI_GUIDE）

> 本文件是给 **AI 助手 / 新加入的开发者** 的导航手册。
> 任何代码修改前，先读这份文档，可以避免大量探索性搜索。
> **修改完代码后，请同步更新本文件（尤其是第 4 节）。**

---

## 1. 系统总览

**项目**：AIGC 营销内容生成平台（个人/小团队版，本地开发优先）

**一句话**：把多个大模型（文案 / 图片 / 视频 / TTS）串成一条流水线，加上品牌知识库（RAG）和规则审核，让小团队快速产出广告文案、好评文案、海报、短视频。

**当前阶段**：STEP 2（FastAPI 骨架已立，有 / + /health 接口）

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
├── frontend/         [未建] ← Next.js 14 + TypeScript + TailwindCSS
└── backend/                  ← FastAPI 骨架（STEP 2 已建）
    ├── pyproject.toml        ← 依赖声明（uv 管理）
    ├── .python-version       ← 锁定 3.12
    ├── README.md             ← 后端启动速查
    ├── .venv/         [运行时] uv 创建的虚拟环境
    └── app/
        ├── main.py           ← FastAPI 入口 + /health
        └── core/
            └── config.py     ← 读 .env 的配置中心
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
| **模型路由层** | `services/llm_router.py`。所有 LLM 调用必须经过它，统一封装：选模型 / 缓存 / 重试 / 成本统计。改模型只动 `.env` 的 `LLM_PROVIDER`。 |
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
| 加 / 改敏感词 | `backend/app/services/compliance/wordlists/*.txt` | 进程启动时加载 |
| 加广告法违禁词 | `backend/app/services/compliance/ad_law.py` 中的列表 | — |
| 改批量好评的"人设池" | `backend/app/services/review_generator.py` 的 `PERSONAS` | — |
| 改批量好评的去重阈值 | 同上文件的 `SIMILARITY_THRESHOLD` | 默认 0.85 |
| 加新的海报模板 | `backend/app/services/poster_composer.py` + `backend/templates/poster/*.json` | — |
| 改视频脚本 Prompt | `backend/app/prompts/video/script.md` | 控制 DeepSeek-V4 脚本格式 |
| 改分镜图生成参数 | `backend/app/workers/video_worker.py` 的 `gen_images()` | Qwen-Image-2.0 分辨率/风格等 |
| 改视频片段生成参数 | `backend/app/workers/video_worker.py` 的 `gen_clips()` | Wan2.7-Video 时长/运动幅度等 |
| 重新生成单张分镜图 | POST `/api/video/retry-image` | 传 `task_id` + `shot_index` |
| 重新生成单个视频片段 | POST `/api/video/retry-clip` | 传 `task_id` + `shot_index` |
| 确认某步进入下一阶段 | POST `/api/video/confirm` | 传 `task_id` + `stage` + 修改后的 `payload` |
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
前端 POST /api/video/start → 立即返回 task_id，stage="pending"
                                    ↓
                        ━━━ STEP 1: 脚本生成 ━━━
                        Celery: video_worker.gen_script()
                            └─ DeepSeek-V4 生成脚本 JSON
                               (含 narration + 每镜头 scene_desc)
                                    ↓
                        更新 video_tasks.stage = "script_done"
                        存脚本 JSON 到 Postgres
                                    ↓
前端轮询到 script_done → 显示脚本编辑卡片（可修改每个 scene_desc）
用户确认 → 前端 POST /api/video/confirm { task_id, stage: "script_done", payload: {...} }
                                    ↓
                        ━━━ STEP 2: 分镜图生成 ━━━
                        Celery: video_worker.gen_images()
                            └─ Qwen-Image-2.0 逐镜头生成图片
                               单张可独立重试
                                    ↓
                        更新 stage = "images_done"
                        存图片 URL 列表到 Postgres + MinIO
                                    ↓
前端轮询到 images_done → 网格展示所有分镜图（可单张重新生成）
用户确认 → 前端 POST /api/video/confirm { task_id, stage: "images_done", payload: {...} }
                                    ↓
                        ━━━ STEP 3: 视频片段生成 ━━━
                        Celery: video_worker.gen_clips()
                            └─ Wan2.7-Video 逐镜头生成 MP4 片段
                               单个片段可独立重试
                                    ↓
                        video_worker.assemble()
                            └─ FFmpeg 拼接 + 字幕 + BGM
                                    ↓
                        更新 stage = "done"，存最终 MP4 到 MinIO
                                    ↓
前端轮询到 done → 显示最终视频预览 + 下载链接
```

`video_tasks.stage` 枚举：`pending` → `script_done` → `images_done` → `clips_done` → `done` | `failed`

---

## 6. 数据库 Schema 速查

> STEP 3 已完成，3 张核心表已建。

| 表名 | 主要字段 | 说明 |
|---|---|---|
| `users` | `id`, `email`(unique), `hashed_password`, `role`(admin/user), `is_active`, `created_at` | JWT 用户体系 |
| `generation_logs` | `id`, `user_id`(FK), `module`, `prompt`, `result`, `model`, `latency_ms`, `created_at` | 所有生成记录 |
| `usage_logs` | `id`, `user_id`(FK), `module`, `model`, `tokens_in`, `tokens_out`, `cost_usd`, `created_at` | 成本统计 |

后续待建：`prompt_templates` / `kb_documents` / `poster_tasks` / `video_tasks`

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
| `LLM_PROVIDER` | 文案模型路由 | `github` |
| `GITHUB_TOKEN` | GitHub Models 鉴权 | — |
| `DASHSCOPE_API_KEY` | DeepSeek-V4 / Qwen3.7-Max / Qwen-Image-2.0 / Qwen-VL / Wan2.7-Video（均走 DashScope） | — |
| `COPY_DRAFT_MODEL` | 文案/策划初稿模型名 | `deepseek-v4` |
| `COPY_POLISH_MODEL` | 文案/策划润色模型名 | `qwen-plus`（Qwen3.7-Max 接口名） |
| `VIDEO_DEEPSEEK_MODEL` | 脚本生成模型名 | `deepseek-v4` |
| `VIDEO_IMAGE_MODEL` | 分镜图生成模型名 | `wanx2.1-t2i-turbo` |
| `VIDEO_CLIP_MODEL` | 视频片段生成模型名 | `wan2.7-14b-text2video` |
| `DATABASE_URL` | Postgres 连接串 | `postgresql+psycopg://...` |
| `REDIS_URL` | Celery + 缓存 | `redis://localhost:6379/0` |
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

**后端（STEP 3 已完成）**：

```bash
cd backend
uv sync                                        # 首次装依赖
uv run uvicorn app.main:app --reload --port 8000
```

- 首页: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health  → `{api/postgres/redis: ok}`
- 注册: POST http://localhost:8000/api/auth/register
- 登录: POST http://localhost:8000/api/auth/login  → 返回 JWT token
- 当前用户: GET http://localhost:8000/api/auth/me  （Bearer token）

**前端**：> [未建] STEP 7 后补充。

---

## 9. 已知限制与 TODO

- 当前处于 **STEP 3 完成**，数据库 + JWT 用户体系已就绪
- GitHub Models 有速率限制（开发期够用，生产期需切换）
- 视频生成 MVP 暂未支持人物口型对齐
- 多语言：当前只考虑中文 + 英文
- 不做企业级特性：多租户 / SSO / 审批流 / 计费

---

## 10. 开发节奏（当前位置 = STEP 3 完成）

```
[✓] STEP 0  脚手架与导航文件
[✓] STEP 1  Docker 基础设施（postgres/redis/qdrant/minio）
[✓] STEP 2  后端骨架（FastAPI hello）
[✓] STEP 3  数据库 + JWT 用户体系
[ ] STEP 4  模型路由层（接 DashScope：DeepSeek-V4 / Qwen3.7-Max）
[ ] STEP 5  Celery 异步任务框架
[ ] STEP 6  规则审核引擎
[ ] STEP 7  广告文案生成（第一个完整功能）
[ ] STEP 8  批量好评生成
─── P1 完成 ───
[ ] STEP 9+ RAG / 海报 / 视频
```

完成每个 STEP 后，请在此处打勾，并更新第 2、4、6、7、8 节相关内容。
