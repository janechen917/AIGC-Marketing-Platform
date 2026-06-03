"use client";

import { FormEvent, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";
import type {
  CopyGenerateRequest,
  CopyGenerateResponse,
} from "@/lib/types";
import { useRequireAuth } from "@/lib/useRequireAuth";
import { ComplianceBadge, ComplianceIssues } from "@/lib/compliance";

const PLATFORMS = ["公众号", "小红书", "微博", "抖音", "X", "Facebook"];
const STYLES = ["专业", "活泼", "高端", "口语化", "情感"];
const LENGTHS = ["短", "中等", "长"];

export default function CopyPage() {
  useRequireAuth();

  const [form, setForm] = useState({
    product_name: "",
    selling_points: "",
    target_audience: "",
    platform: PLATFORMS[0],
    style: STYLES[0],
    length_hint: LENGTHS[1],
    title_count: 3,
    brand_name: "",
    required_phrases: "",
    forbidden_competitors: "",
    require_hashtag: true,
    require_cta: true,
    max_emojis: 6,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CopyGenerateResponse | null>(null);

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

    const payload: CopyGenerateRequest = {
      product_name: form.product_name,
      selling_points: points,
      target_audience: form.target_audience,
      platform: form.platform,
      style: form.style,
      length_hint: form.length_hint,
      title_count: form.title_count,
      brand_name: form.brand_name || null,
      required_phrases: splitLines(form.required_phrases),
      forbidden_competitors: splitLines(form.forbidden_competitors),
      require_hashtag: form.require_hashtag,
      require_cta: form.require_cta,
      max_emojis: form.max_emojis,
    };

    setLoading(true);
    try {
      const res = await apiRequest<CopyGenerateResponse>(
        "/api/copy/generate",
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

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
      >
        <h2 className="text-lg font-semibold">广告文案生成</h2>

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

        <Field label="目标人群">
          <input
            required
            value={form.target_audience}
            onChange={(e) =>
              setForm({ ...form, target_audience: e.target.value })
            }
            className={inputCls}
          />
        </Field>

        <div className="grid grid-cols-3 gap-3">
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
          <Field label="长度">
            <select
              value={form.length_hint}
              onChange={(e) =>
                setForm({ ...form, length_hint: e.target.value })
              }
              className={inputCls}
            >
              {LENGTHS.map((l) => (
                <option key={l}>{l}</option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="品牌名（可选）">
          <input
            value={form.brand_name}
            onChange={(e) =>
              setForm({ ...form, brand_name: e.target.value })
            }
            className={inputCls}
          />
        </Field>

        <Field label="必含短语（可选）">
          <input
            value={form.required_phrases}
            onChange={(e) =>
              setForm({ ...form, required_phrases: e.target.value })
            }
            className={inputCls}
            placeholder="逗号分隔"
          />
        </Field>

        <Field label="禁提竞品（可选）">
          <input
            value={form.forbidden_competitors}
            onChange={(e) =>
              setForm({ ...form, forbidden_competitors: e.target.value })
            }
            className={inputCls}
            placeholder="逗号分隔"
          />
        </Field>

        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.require_hashtag}
              onChange={(e) =>
                setForm({ ...form, require_hashtag: e.target.checked })
              }
            />
            需要 #话题
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.require_cta}
              onChange={(e) =>
                setForm({ ...form, require_cta: e.target.checked })
              }
            />
            需要 CTA
          </label>
          <label className="flex items-center gap-2">
            最多 emoji
            <input
              type="number"
              min={0}
              max={20}
              value={form.max_emojis}
              onChange={(e) =>
                setForm({ ...form, max_emojis: Number(e.target.value) })
              }
              className="w-16 rounded border border-slate-300 px-2 py-1 text-sm"
            />
          </label>
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
          {loading ? "生成中…（约 5–20 秒）" : "生成文案"}
        </button>
      </form>

      <div className="space-y-4">
        {result ? (
          <>
            <section className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-base font-semibold">润色稿</h3>
                <ComplianceBadge compliance={result.compliance} />
              </div>
              <pre className="whitespace-pre-wrap break-words text-sm text-slate-800">
                {result.polished_text}
              </pre>
              <p className="mt-3 text-xs text-slate-400">
                模型：{result.polish_model}
              </p>
              <div className="mt-3">
                <ComplianceIssues compliance={result.compliance} />
              </div>
            </section>

            <details className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <summary className="cursor-pointer text-base font-semibold">
                初稿（{result.draft_model}）
              </summary>
              <pre className="mt-3 whitespace-pre-wrap break-words text-sm text-slate-600">
                {result.draft_text}
              </pre>
            </details>
          </>
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
