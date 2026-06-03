"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, ApiError } from "@/lib/api";
import { setToken } from "@/lib/auth";

type LoginResponse = {
  access_token: string;
  token_type: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // 后端 /api/auth/login 使用 OAuth2PasswordRequestForm，需要 form 编码，字段名 username
      const res = await apiRequest<LoginResponse>("/api/auth/login", {
        method: "POST",
        form: true,
        auth: false,
        body: { username: email, password },
      });
      setToken(res.access_token);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.detail === "object" && err.detail !== null
            ? (err.detail as { detail?: string }).detail
            : null;
        setError(detail ?? `登录失败 (${err.status})`);
      } else {
        setError("网络错误，请稍后重试");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-5 rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200"
      >
        <div>
          <h1 className="text-2xl font-semibold">登录</h1>
          <p className="mt-1 text-sm text-slate-500">
            AIGC 营销平台 · 开发版
          </p>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium" htmlFor="email">
            邮箱
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium" htmlFor="password">
            密码
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
          />
        </div>

        {error && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
        >
          {loading ? "登录中…" : "登录"}
        </button>

        <p className="text-xs text-slate-500">
          还没账号？请用后端 <code>POST /api/auth/register</code> 创建。
        </p>
      </form>
    </main>
  );
}
