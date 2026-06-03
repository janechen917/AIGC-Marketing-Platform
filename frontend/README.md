# Frontend (Next.js 14)

AIGC 营销平台的前端，App Router + TypeScript + TailwindCSS。

## 启动

```bash
cd frontend
cp .env.local.example .env.local   # 调整 NEXT_PUBLIC_API_BASE
npm install
npm run dev
```

浏览器打开 http://localhost:3000，会自动跳转到 `/login`。

> 登录前请先用后端创建账号：
> `POST http://localhost:8000/api/auth/register {"email":"...","password":"..."}`

## 当前页面（前端 STEP 11 第一版）

- `/login` — 邮箱+密码登录，调用 `POST /api/auth/login`
- `/dashboard` — 展示 `GET /api/auth/me` + `GET /health`
- `/copy` — 广告文案表单，调用 `POST /api/copy/generate`，展示初稿/润色/合规结果
- `/reviews` — 批量好评生成，调用 `POST /api/reviews/generate`，支持 CSV 下载
- `/poster` — 海报生成，调用 `POST /api/poster/generate`，轮询 `GET /api/poster/{id}`
- `/video` — 视频生成（STEP 11 第一版），当前非交付阻塞项
- `/tasks` — 投递 `/api/tasks/{ping,video-demo}`，表格轮询状态

当前优先交付页面：`/copy`、`/reviews`、`/poster`。
视频已接入 FFmpeg 合成，后续按需求增强向量检索、视频模型与音频字幕。

## 当前推荐测试顺序

1. `/copy`：验证文案生成 + 合规展示
2. `/reviews`：验证批量生成 + CSV 下载
3. `/poster`：验证异步出图 + 轮询展示

## 目录

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  → 跳转 /login
│   ├── globals.css
│   ├── (auth)/login/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx            顶部导航 + 退出
│       ├── dashboard/page.tsx    概览页
│       ├── copy/page.tsx         广告文案
│       ├── reviews/page.tsx      批量好评
│       ├── poster/page.tsx       海报生成
│       ├── video/page.tsx        视频生成（STEP 11 第一版）
│       └── tasks/page.tsx        任务控制台
├── lib/
│   ├── api.ts                    fetch 封装（自动带 JWT）
│   ├── auth.ts                   localStorage token 读写
│   ├── useRequireAuth.ts         未登录跳 /login
│   ├── compliance.tsx            合规徽章/issue 渲染
│   └── types.ts                  与后端 schema 对齐
├── package.json
├── tsconfig.json
├── next.config.mjs
├── tailwind.config.ts
└── postcss.config.mjs
```
