"use client";

import { useEffect, useRef, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";
import type { PosterTaskResponse } from "@/lib/types";
import { useRequireAuth } from "@/lib/useRequireAuth";

const SIZE_OPTIONS = [
  { value: "1024*1024", label: "正方形 1024×1024" },
  { value: "1024*768", label: "横版 1024×768" },
  { value: "768*1024", label: "竖版 768×1024" },
];

const TERMINAL = new Set(["done", "failed"]);

export default function PosterPage() {
  useRequireAuth();

  const [prompt, setPrompt] = useState("");
  const [size, setSize] = useState("1024*1024");
  const [task, setTask] = useState<PosterTaskResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) {
      setError("请输入海报提示词");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const res = await apiRequest<PosterTaskResponse>(
        "/api/poster/generate",
        {
          method: "POST",
          body: { prompt: prompt.trim(), size },
        },
      );
      setTask(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`提交失败 (${err.status})`);
      } else {
        setError("网络错误");
      }
    } finally {
      setSubmitting(false);
    }
  }

  useEffect(() => {
    if (!task || TERMINAL.has(task.status)) {
      if (pollingRef.current) clearInterval(pollingRef.current);
      return;
    }
    const id = task.id;
    pollingRef.current = setInterval(async () => {
      try {
        const next = await apiRequest<PosterTaskResponse>(
          `/api/poster/${id}`,
        );
        setTask(next);
      } catch {
        /* 静默重试 */
      }
    }, 1500);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [task]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">海报生成</h2>
        <p className="mt-1 text-sm text-slate-500">
          调用 DashScope 文生图（异步），生成完成后图片会上传到 MinIO 并返回 URL。
        </p>
        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">
              提示词
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              maxLength={2000}
              placeholder="例如：夏日清凉饮料海报，蓝色背景，冰块四溅，电商风格"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">
              尺寸
            </label>
            <select
              value={size}
              onChange={(e) => setSize(e.target.value)}
              className="mt-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {SIZE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {submitting ? "提交中…" : "生成海报"}
          </button>
          {error && (
            <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}
        </form>
      </section>

      {task && (
        <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">任务详情</h3>
            <StatusBadge status={task.status} />
          </div>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
            <dt>ID</dt>
            <dd className="font-mono break-all">{task.id}</dd>
            <dt>模型</dt>
            <dd>{task.model_used}</dd>
            <dt>尺寸</dt>
            <dd>{task.size}</dd>
            <dt>创建时间</dt>
            <dd>{task.created_at}</dd>
          </dl>

          {task.status === "failed" && task.error && (
            <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {task.error}
            </div>
          )}

          {task.status === "done" && task.image_url && (
            <div className="mt-4">
              <a
                href={task.image_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-blue-600 underline"
              >
                {task.image_url}
              </a>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={task.image_url}
                alt="生成的海报"
                className="mt-3 max-h-[640px] rounded-lg border border-slate-200"
              />
            </div>
          )}

          {(task.status === "pending" || task.status === "running") && (
            <div className="mt-4 text-sm text-slate-500">
              生成中，1.5 秒轮询一次……
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "done"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : status === "failed"
        ? "bg-red-50 text-red-700 ring-red-200"
        : status === "running"
          ? "bg-blue-50 text-blue-700 ring-blue-200"
          : "bg-slate-50 text-slate-600 ring-slate-200";
  return (
    <span
      className={`inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1 ${color}`}
    >
      {status}
    </span>
  );
}
