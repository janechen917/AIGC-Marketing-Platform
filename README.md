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

**STEP 0：脚手架与导航文件** ✅

后续步骤见 [AI_GUIDE.md 第 10 节](AI_GUIDE.md#10-开发节奏当前位置--step-0)。

---

## 技术栈

- 前端：Next.js 14 + TypeScript + TailwindCSS + Polotno
- 后端：FastAPI + Celery + SQLAlchemy + Alembic
- 数据：PostgreSQL + Redis + Qdrant + MinIO
- 模型：GitHub Models (gpt-4o-mini) → 后续切 Qwen3 / DeepSeek / Qwen-Image-2.0 / Wan2.7-Video

---

## 快速开始

> ⚠️ STEP 1 完成后才有可运行的环境。当前仓库只有文档与目录占位。

预期启动流程（参考）：

```bash
cp .env.example .env             # 填入 GITHUB_TOKEN 等
docker compose up -d             # 启动基础设施
cd backend && uv sync && uv run uvicorn app.main:app --reload
cd frontend && pnpm install && pnpm dev
```
