"use client";

import { useEffect, useRef, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";
import type {
  TaskEnqueueResponse,
  TaskStatusResponse,
} from "@/lib/types";
import { useRequireAuth } from "@/lib/useRequireAuth";

type TaskRow = {
  id: string;
  name: string;
  state: string;
  result?: unknown;
  error?: string;
  finished: boolean;
};

const TERMINAL_STATES = new Set(["SUCCESS", "FAILURE", "REVOKED"]);

export default function TasksPage() {
  useRequireAuth();

  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  async function enqueue(path: string, label: string) {
    setError(null);
    try {
      const res = await apiRequest<TaskEnqueueResponse>(path, {
        method: "POST",
      });
      setTasks((prev) => [
        {
          id: res.task_id,
          name: res.task_name || label,
          state: res.state,
          finished: false,
        },
        ...prev,
      ]);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`投递失败 (${err.status})`);
      } else {
        setError("网络错误");
      }
    }
  }

  useEffect(() => {
    async function poll() {
      const pending = tasks.filter((t) => !t.finished);
      if (pending.length === 0) return;

      const updates = await Promise.all(
        pending.map(async (t) => {
          try {
            const s = await apiRequest<TaskStatusResponse>(
              `/api/tasks/${t.id}`,
            );
            return { id: t.id, status: s };
          } catch {
            return { id: t.id, status: null };
          }
        }),
      );

      setTasks((prev) =>
        prev.map((t) => {
          const u = updates.find((x) => x.id === t.id);
          if (!u || !u.status) return t;
          return {
            ...t,
            state: u.status.state,
            result: u.status.result,
            error: u.status.error,
            finished: TERMINAL_STATES.has(u.status.state),
          };
        }),
      );
    }

    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(poll, 1500);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [tasks]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">Celery 异步任务</h2>
        <p className="mt-1 text-sm text-slate-500">
          下面两个按钮分别投递后端 <code>/api/tasks/*</code> 中的示例任务。
          海报已迁移至 <a href="/poster" className="text-blue-600 underline">/poster</a>（STEP 9 实接入）。
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            onClick={() => enqueue("/api/tasks/ping", "ping")}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800"
          >
            投递 ping
          </button>
          <button
            onClick={() => enqueue("/api/tasks/video-demo", "video.generate")}
            className="rounded-lg bg-slate-700 px-4 py-2 text-sm text-white hover:bg-slate-600"
          >
            投递 video-demo
          </button>
        </div>
        {error && (
          <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
      </section>

      <section className="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Task ID</th>
              <th className="px-4 py-2">名称</th>
              <th className="px-4 py-2">状态</th>
              <th className="px-4 py-2">结果 / 错误</th>
            </tr>
          </thead>
          <tbody>
            {tasks.length === 0 ? (
              <tr>
                <td
                  colSpan={4}
                  className="px-4 py-6 text-center text-slate-400"
                >
                  还没有任务，点上方按钮试一下。
                </td>
              </tr>
            ) : (
              tasks.map((t) => (
                <tr key={t.id} className="border-b border-slate-100">
                  <td className="px-4 py-2 font-mono text-xs">{t.id}</td>
                  <td className="px-4 py-2">{t.name}</td>
                  <td className="px-4 py-2">
                    <StateBadge state={t.state} />
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-600">
                    {t.error ? (
                      <span className="text-red-600">{t.error}</span>
                    ) : t.result !== undefined ? (
                      <code className="break-all">
                        {JSON.stringify(t.result)}
                      </code>
                    ) : (
                      <span className="text-slate-400">轮询中…</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function StateBadge({ state }: { state: string }) {
  const color =
    state === "SUCCESS"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : state === "FAILURE"
        ? "bg-red-50 text-red-700 ring-red-200"
        : state === "STARTED"
          ? "bg-blue-50 text-blue-700 ring-blue-200"
          : "bg-slate-50 text-slate-600 ring-slate-200";
  return (
    <span
      className={`inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1 ${color}`}
    >
      {state}
    </span>
  );
}
