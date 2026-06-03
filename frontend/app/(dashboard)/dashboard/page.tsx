"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, ApiError } from "@/lib/api";
import { clearToken } from "@/lib/auth";

type CurrentUser = {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

type HealthStatus = {
  api: string;
  postgres: string;
  redis: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const me = await apiRequest<CurrentUser>("/api/auth/me");
        if (!cancelled) setUser(me);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          clearToken();
          router.replace("/login");
          return;
        }
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "加载失败");
        }
      }

      try {
        const h = await apiRequest<HealthStatus>("/health", { auth: false });
        if (!cancelled) setHealth(h);
      } catch {
        if (!cancelled) setHealth(null);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">当前用户</h2>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        {user ? (
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <dt className="text-slate-500">邮箱</dt>
            <dd>{user.email}</dd>
            <dt className="text-slate-500">角色</dt>
            <dd>{user.role}</dd>
            <dt className="text-slate-500">激活</dt>
            <dd>{user.is_active ? "是" : "否"}</dd>
            <dt className="text-slate-500">创建时间</dt>
            <dd>{new Date(user.created_at).toLocaleString()}</dd>
          </dl>
        ) : !error ? (
          <p className="mt-2 text-sm text-slate-500">加载中…</p>
        ) : null}
      </section>

      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">服务健康</h2>
        {health ? (
          <ul className="mt-3 space-y-1 text-sm">
            <li>API：<StatusDot ok={health.api === "ok"} /> {health.api}</li>
            <li>Postgres：<StatusDot ok={health.postgres === "ok"} /> {health.postgres}</li>
            <li>Redis：<StatusDot ok={health.redis === "ok"} /> {health.redis}</li>
          </ul>
        ) : (
          <p className="mt-2 text-sm text-slate-500">无法访问 /health</p>
        )}
      </section>

      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">后续</h2>
        <p className="mt-2 text-sm text-slate-600">
          广告文案 / 批量好评 / 任务页将在前端 STEP 2 接入。
          海报与视频页面等待 STEP 9+ 后端 Worker 真实接通。
        </p>
      </section>
    </div>
  );
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${
        ok ? "bg-emerald-500" : "bg-red-500"
      }`}
    />
  );
}
