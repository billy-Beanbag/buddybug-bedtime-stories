"use client";

import Link from "next/link";

import type { ModerationCaseRead } from "@/lib/types";

function severityClasses(severity: string) {
  if (severity === "critical") {
    return "bg-rose-100 text-rose-700";
  }
  if (severity === "high") {
    return "bg-amber-100 text-amber-700";
  }
  if (severity === "medium") {
    return "bg-sky-100 text-sky-700";
  }
  return "bg-slate-100 text-slate-700";
}

export function ModerationCaseTable({ cases }: { cases: ModerationCaseRead[] }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Case</th>
              <th className="px-4 py-3 font-medium">Severity</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Assignee</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {cases.map((item) => (
              <tr key={item.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{item.summary}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    #{item.id} • {item.case_type} • {item.target_type}
                    {item.target_id ? ` #${item.target_id}` : ""}
                  </div>
                </td>
                <td className="px-4 py-4 align-top">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${severityClasses(item.severity)}`}>{item.severity}</span>
                </td>
                <td className="px-4 py-4 align-top">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{item.status}</span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {item.source_type}
                  {item.source_id ? ` #${item.source_id}` : ""}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {item.assigned_to_user_id ? `User #${item.assigned_to_user_id}` : "Unassigned"}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{new Date(item.updated_at).toLocaleString()}</td>
                <td className="px-4 py-4 align-top">
                  <Link
                    href={`/admin/moderation/${item.id}`}
                    className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                  >
                    Open case
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
