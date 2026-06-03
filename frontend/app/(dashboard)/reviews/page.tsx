"use client";

import { FormEvent, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";
import type {
  ReviewsGenerateRequest,
  ReviewsGenerateResponse,
} from "@/lib/types";
import { useRequireAuth } from "@/lib/useRequireAuth";

const PLATFORMS = ["小红书", "淘宝", "京东", "微博", "抖音"];
const STYLES = ["真实口碑", "种草", "对比测评", "理性专业"];

export default function ReviewsPage() {
  useRequireAuth();

  const [form, setForm] = useState({
    product_name: "",
    selling_points: "",
    platform: PLATFORMS[0],
    style: STYLES[0],
    target_count: 20,
    batch_size: 8,
    max_rounds: 10,
    similarity_threshold: 0.85,
    persona_pool: "宝妈, 学生, 上班族, 数码爱好者, 新手用户",
    require_hashtag: false,
    require_cta: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReviewsGenerateResponse | null>(null);

  function splitLines(text: string): string[] {
    return text
      .split(/[\n,，;；]/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    const points = splitLines(form.selling_points);
    if (points.length === 0) {
      setError("请至少填写一条卖点");
      return;
    }

    if (!form.product_name.trim()) {
      setError("请填写产品名");
      return;
    }

    const targetCount = Math.min(100, Math.max(1, Number(form.target_count) || 1));
    const batchSize = Math.min(20, Math.max(1, Number(form.batch_size) || 1));
    const maxRounds = Math.min(50, Math.max(1, Number(form.max_rounds) || 1));
    const similarityThreshold = Math.min(
      0.99,
      Math.max(0.5, Number(form.similarity_threshold) || 0.85),
    );

    const payload: ReviewsGenerateRequest = {
      product_name: form.product_name.trim(),
      selling_points: points,
      platform: form.platform,
      style: form.style,
      target_count: targetCount,
      batch_size: batchSize,
      max_rounds: maxRounds,
      similarity_threshold: similarityThreshold,
      persona_pool: splitLines(form.persona_pool),
      require_hashtag: form.require_hashtag,
      require_cta: form.require_cta,
    };

    setLoading(true);
    try {
      const res = await apiRequest<ReviewsGenerateResponse>(
        "/api/reviews/generate",
        { method: "POST", body: payload },
      );
      setResult(res);
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.detail === "object" && err.detail !== null
            ? (err.detail as { detail?: string }).detail
            : null;
        setError(detail ?? `请求失败 (${err.status})`);
      } else {
        setError("网络错误");
      }
    } finally {
      setLoading(false);
    }
  }

  function downloadCsv() {
    if (!result) return;
    const blob = new Blob(["\ufeff", result.csv_content], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const safeName = (form.product_name.trim() || "export")
      .replace(/[\\/:*?"<>|\s]+/g, "_")
      .slice(0, 60);
    a.download = `reviews_${safeName}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
      >
        <h2 className="text-lg font-semibold">批量好评生成</h2>

        <Field label="产品名">
          <input
            required
            value={form.product_name}
            onChange={(e) =>
              setForm({ ...form, product_name: e.target.value })
            }
            className={inputCls}
          />
        </Field>

        <Field label="卖点（换行或逗号分隔）">
          <textarea
            required
            rows={3}
            value={form.selling_points}
            onChange={(e) =>
              setForm({ ...form, selling_points: e.target.value })
            }
            className={inputCls}
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="平台">
            <select
              value={form.platform}
              onChange={(e) => setForm({ ...form, platform: e.target.value })}
              className={inputCls}
            >
              {PLATFORMS.map((p) => (
                <option key={p}>{p}</option>
              ))}
            </select>
          </Field>
          <Field label="风格">
            <select
              value={form.style}
              onChange={(e) => setForm({ ...form, style: e.target.value })}
              className={inputCls}
            >
              {STYLES.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="人设池（逗号分隔）">
          <input
            value={form.persona_pool}
            onChange={(e) =>
              setForm({ ...form, persona_pool: e.target.value })
            }
            className={inputCls}
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.require_hashtag}
              onChange={(e) =>
                setForm({ ...form, require_hashtag: e.target.checked })
              }
            />
            需要包含 #话题
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.require_cta}
              onChange={(e) => setForm({ ...form, require_cta: e.target.checked })}
            />
            需要包含 CTA
          </label>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Field label="目标条数">
            <input
              type="number"
              min={1}
              max={100}
              value={form.target_count}
              onChange={(e) =>
                setForm({ ...form, target_count: Number(e.target.value) })
              }
              className={inputCls}
            />
          </Field>
          <Field label="每轮数量">
            <input
              type="number"
              min={1}
              max={20}
              value={form.batch_size}
              onChange={(e) =>
                setForm({ ...form, batch_size: Number(e.target.value) })
              }
              className={inputCls}
            />
          </Field>
          <Field label="最大轮数">
            <input
              type="number"
              min={1}
              max={50}
              value={form.max_rounds}
              onChange={(e) =>
                setForm({ ...form, max_rounds: Number(e.target.value) })
              }
              className={inputCls}
            />
          </Field>
          <Field label="去重阈值">
            <input
              type="number"
              min={0.5}
              max={0.99}
              step={0.01}
              value={form.similarity_threshold}
              onChange={(e) =>
                setForm({
                  ...form,
                  similarity_threshold: Number(e.target.value),
                })
              }
              className={inputCls}
            />
          </Field>
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
          {loading ? "生成中…（取决于目标条数）" : "生成好评"}
        </button>
      </form>

      <div className="space-y-4">
        {result ? (
          <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-base font-semibold">
                生成结果 · {result.total_generated} 条
              </h3>
              <button
                onClick={downloadCsv}
                className="rounded-md bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-800"
              >
                下载 CSV
              </button>
            </div>
            <p className="mb-3 text-xs text-slate-500">
              轮数 {result.rounds} · 去重剔除 {result.deduped_dropped} · 合规剔除 {result.compliance_dropped}
            </p>
            <ol className="max-h-[60vh] space-y-2 overflow-auto text-sm">
              {result.reviews.map((r, i) => (
                <li
                  key={i}
                  className="rounded-md bg-slate-50 px-3 py-2 ring-1 ring-slate-200"
                >
                  <span className="mr-2 font-mono text-xs text-slate-400">
                    #{i + 1}
                  </span>
                  {r}
                </li>
              ))}
            </ol>
          </section>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/50 p-10 text-center text-sm text-slate-400">
            填写左侧表单后生成
          </div>
        )}
      </div>
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none";

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-slate-700">{label}</label>
      {children}
    </div>
  );
}
