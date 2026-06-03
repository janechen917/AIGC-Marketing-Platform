import type { ComplianceCheckResponse } from "@/lib/types";

const LEVEL_COLOR: Record<string, string> = {
  error: "bg-red-50 text-red-700 ring-red-200",
  warn: "bg-amber-50 text-amber-700 ring-amber-200",
  info: "bg-slate-50 text-slate-700 ring-slate-200",
};

export function ComplianceBadge({
  compliance,
}: {
  compliance: ComplianceCheckResponse;
}) {
  if (compliance.passed) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
        ✓ 合规通过
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-red-200">
      ✗ 命中 {compliance.issue_count} 条
    </span>
  );
}

export function ComplianceIssues({
  compliance,
}: {
  compliance: ComplianceCheckResponse;
}) {
  if (compliance.issues.length === 0) return null;
  return (
    <ul className="space-y-1 text-sm">
      {compliance.issues.map((it, i) => (
        <li
          key={i}
          className={`rounded-md px-2 py-1 ring-1 ${
            LEVEL_COLOR[it.level] ?? LEVEL_COLOR.info
          }`}
        >
          <span className="font-mono text-xs opacity-70">[{it.rule}]</span>{" "}
          {it.message}
        </li>
      ))}
    </ul>
  );
}
