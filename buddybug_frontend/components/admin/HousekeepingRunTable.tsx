"use client";

import type { HousekeepingRunRead } from "@/lib/types";

function statusClasses(status: string) {
  if (status === "succeeded") {
    return "bg-emerald-50 text-emerald-700";
  }
  if (status === "failed") {
    return "bg-rose-50 text-rose-700";
  }
  if (status === "running") {
    return "bg-amber-50 text-amber-700";
  }
  return "bg-slate-100 text-slate-700";
}

export function HousekeepingRunTable({
  runs,
}: {
  runs: HousekeepingRunRead[];
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Run</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Dry run</th>
              <th className="px-4 py-3 font-medium">Candidates</th>
              <th className="px-4 py-3 font-medium">Affected</th>
              <th className="px-4 py-3 font-medium">Completed</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {runs.map((run) => (
              <tr key={run.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">Run #{run.id}</div>
                  <div className="mt-1 text-xs text-slate-500">Policy #{run.policy_id}</div>
                  {run.error_message ? <p className="mt-2 max-w-lg text-rose-700">{run.error_message}</p> : null}
                </td>
                <td className="px-4 py-4 align-top">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(run.status)}`}>{run.status}</span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{run.dry_run ? "yes" : "no"}</td>
                <td className="px-4 py-4 align-top text-slate-700">{run.candidate_count}</td>
                <td className="px-4 py-4 align-top text-slate-700">{run.affected_count}</td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {run.completed_at ? new Date(run.completed_at).toLocaleString() : "In progress"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
