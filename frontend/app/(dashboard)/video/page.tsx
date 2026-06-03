"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, apiRequest } from "@/lib/api";
import type { VideoTaskResponse } from "@/lib/types";
import { useRequireAuth } from "@/lib/useRequireAuth";

const TERMINAL = new Set(["done", "failed"]);

export default function VideoPage() {
  useRequireAuth();

  const [prompt, setPrompt] = useState("");
  const [shotCount, setShotCount] = useState(3);
  const [task, setTask] = useState<VideoTaskResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loadingAction, setLoadingAction] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  async function handleStart(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) {
      setError("请输入视频主题");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await apiRequest<VideoTaskResponse>("/api/video/start", {
        method: "POST",
        body: { prompt: prompt.trim(), shot_count: shotCount },
      });
      setTask(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`启动失败 (${err.status})`);
      } else {
        setError("网络错误");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function confirmStage(stage: "script_done" | "images_done") {
    if (!task) return;
    setLoadingAction(true);
    setError(null);
    try {
      const res = await apiRequest<VideoTaskResponse>("/api/video/confirm", {
        method: "POST",
        body: {
          video_id: task.id,
          stage,
          payload: stage === "script_done" ? { script_data: task.script_data } : {},
        },
      });
      setTask(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`确认失败 (${err.status})`);
      } else {
        setError("网络错误");
      }
    } finally {
      setLoadingAction(false);
    }
  }

  useEffect(() => {
    if (!task || TERMINAL.has(task.status)) {
      if (pollingRef.current) clearInterval(pollingRef.current);
      return;
    }

    pollingRef.current = setInterval(async () => {
      try {
        const next = await apiRequest<VideoTaskResponse>(`/api/video/${task.id}`);
        setTask(next);
      } catch {
        // 静默重试
      }
    }, 1500);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [task]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
        <h2 className="text-lg font-semibold">视频生成（STEP 11 第一版）</h2>
        <p className="mt-1 text-sm text-slate-500">
          当前流程：脚本生成（含检索上下文）→ 人工确认 → 分镜图生成 → 人工确认 → FFmpeg 合成。
        </p>

        <form onSubmit={handleStart} className="mt-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">视频主题</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              maxLength={2000}
              placeholder="例如：夏日清凉饮料 15 秒广告，突出清爽与年轻活力"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">镜头数</label>
            <input
              type="number"
              min={1}
              max={12}
              value={shotCount}
              onChange={(e) => setShotCount(Number(e.target.value || 3))}
              className="mt-1 w-40 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {submitting ? "启动中..." : "启动视频任务"}
          </button>
        </form>

        {error && (
          <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
        )}
      </section>

      {task && (
        <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold">任务详情</h3>
            <StageBadge stage={task.stage} />
          </div>

          <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
            <dt>ID</dt>
            <dd className="font-mono break-all">{task.id}</dd>
            <dt>状态</dt>
            <dd>{task.status}</dd>
            <dt>镜头数</dt>
            <dd>{task.shot_count}</dd>
            <dt>脚本模型</dt>
            <dd>{task.script_model}</dd>
            <dt>分镜模型</dt>
            <dd>{task.image_model}</dd>
            <dt>视频模型</dt>
            <dd>{task.clip_model}</dd>
          </dl>

          {task.script_data && (
            <div className="mt-4 rounded-lg bg-slate-50 p-3">
              <div className="text-sm font-medium">脚本 JSON</div>
              <pre className="mt-2 overflow-auto text-xs text-slate-700">
                {JSON.stringify(task.script_data, null, 2)}
              </pre>
            </div>
          )}

          {task.image_urls && task.image_urls.length > 0 && (
            <div className="mt-4 space-y-1">
              <div className="text-sm font-medium">分镜图 URL</div>
              {task.image_urls.map((u) => (
                <a
                  key={u}
                  href={u}
                  target="_blank"
                  rel="noreferrer"
                  className="block text-xs text-blue-600 underline"
                >
                  {u}
                </a>
              ))}
            </div>
          )}

          {task.clip_urls && task.clip_urls.length > 0 && (
            <div className="mt-4 space-y-1">
              <div className="text-sm font-medium">视频片段 URL</div>
              {task.clip_urls.map((u) => (
                <a
                  key={u}
                  href={u}
                  target="_blank"
                  rel="noreferrer"
                  className="block text-xs text-blue-600 underline"
                >
                  {u}
                </a>
              ))}
            </div>
          )}

          {task.final_video_url && (
            <div className="mt-4">
              <a
                href={task.final_video_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-blue-600 underline"
              >
                最终视频：{task.final_video_url}
              </a>
            </div>
          )}

          {task.error && (
            <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{task.error}</div>
          )}

          <div className="mt-4 flex flex-wrap gap-3">
            {task.stage === "script_done" && task.status === "waiting_confirm" && (
              <button
                onClick={() => confirmStage("script_done")}
                disabled={loadingAction}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500 disabled:opacity-50"
              >
                确认脚本并生成分镜图
              </button>
            )}

            {task.stage === "images_done" && task.status === "waiting_confirm" && (
              <button
                onClick={() => confirmStage("images_done")}
                disabled={loadingAction}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                确认分镜图并生成视频
              </button>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

function StageBadge({ stage }: { stage: string }) {
  const color =
    stage === "done"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
      : stage === "images_done"
        ? "bg-blue-50 text-blue-700 ring-blue-200"
        : stage === "script_done"
          ? "bg-amber-50 text-amber-700 ring-amber-200"
          : stage === "failed"
            ? "bg-red-50 text-red-700 ring-red-200"
            : "bg-slate-50 text-slate-600 ring-slate-200";

  return (
    <span className={`inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1 ${color}`}>
      {stage}
    </span>
  );
}
