# AIGC Marketing Platform

面向个人或小团队人的轻量级 AIGC 营销内容生成平台。
统一界面 + 品牌知识库，把多个大模型串成一条流水线，快速产出：

- 多平台广告文案（公众号 / 小红书 / 微博 / X / Facebook）
- 社媒批量好评文案
- 营销海报（AI 底图 + 可编辑画布）
- 图文短视频（图片 + TTS + FFmpeg）

---

## 文档导航

- **[AI_GUIDE_INDEX.md](AI_GUIDE_INDEX.md)** — AI 助手入口（让 AI 改代码前必读）
- **[AI_GUIDE.md](AI_GUIDE.md)** — 系统总览、目录地图、修改场景定位表
- **[docs/plan.md](docs/plan.md)** — 完整产品方案（v3）

---

## 当前状态

**技术状态：STEP 11 第一版已完成**。

**当前执行优先级（落地优先）**：
- 文案策划（/copy）
- 批量好评（/reviews）
- AIGC 图片（/poster）

视频能力先保持可运行，不作为当前交付阻塞项。

后续步骤见 [AI_GUIDE.md 第 9 节](AI_GUIDE.md#9-已知限制与-todo) 和 [AI_GUIDE.md 第 10 节](AI_GUIDE.md#10-开发节奏当前位置--step-11-第一版完成)。

---

## 技术栈

- 前端：Next.js 14 + TypeScript + TailwindCSS + Polotno
- 后端：FastAPI + Celery + SQLAlchemy + Alembic
- 数据：PostgreSQL + Redis + Qdrant + MinIO
- 模型：GitHub Models (gpt-4o-mini) → 后续切 Qwen3 / DeepSeek / Qwen-Image-2.0 / Wan2.7-Video

---

## 快速开始

```bash
cp .env.example .env             # 填入 DASHSCOPE_API_KEY 等
docker compose up -d             # 启动基础设施
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000
# 另一个终端：
cd frontend && cp .env.local.example .env.local && npm install && npm run dev
```

- 后端：http://localhost:8000  （文档 /docs，健康 /health）
- 前端：http://localhost:3000  （自动跳 /login）

## 当前推荐测试（先跑这三块）

文案验收样例（固定输入与验收标准）：`docs/copy_acceptance_cases.md`

批量好评验收样例（固定输入与验收标准）：`docs/reviews_acceptance_cases.md`

```bash
cd backend
uv run pytest -q tests/test_copywriter.py tests/test_reviews.py tests/test_poster.py

cd ../frontend
npm run build
```
