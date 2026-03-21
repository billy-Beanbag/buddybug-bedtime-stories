"use client";

import type { MaintenanceJobRead } from "@/lib/types";

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
  if (status === "canceled") {
    return "bg-slate-100 text-slate-700";
  }
  return "bg-sky-50 text-sky-700";
}

export function MaintenanceJobTable({
  jobs,
  selectedJobId,
  runningId,
  cancelingId,
  onSelect,
  onRun,
  onCancel,
}: {
  jobs: MaintenanceJobRead[];
  selectedJobId: number | null;
  runningId: number | null;
  cancelingId: number | null;
  onSelect: (job: MaintenanceJobRead) => void;
  onRun: (job: MaintenanceJobRead) => Promise<void>;
  onCancel: (job: MaintenanceJobRead) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Job</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Scope</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {jobs.map((job) => (
              <tr key={job.id} className={selectedJobId === job.id ? "bg-slate-50/70" : undefined}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{job.title}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {job.key} • #{job.id}
                  </div>
                  {job.description ? <p className="mt-2 max-w-xl text-slate-600">{job.description}</p> : null}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{job.job_type}</td>
                <td className="px-4 py-4 align-top">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(job.status)}`}>{job.status}</span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{job.target_scope || "all"}</td>
                <td className="px-4 py-4 align-top text-slate-700">{new Date(job.updated_at).toLocaleString()}</td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onSelect(job)}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                    >
                      View
                    </button>
                    {job.status === "pending" || job.status === "failed" ? (
                      <button
                        type="button"
                        onClick={() => void onRun(job)}
                        disabled={runningId === job.id}
                        className="rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2 font-medium text-emerald-700 disabled:opacity-60"
                      >
                        {runningId === job.id ? "Running..." : "Run"}
                      </button>
                    ) : null}
                    {job.status === "pending" ? (
                      <button
                        type="button"
                        onClick={() => void onCancel(job)}
                        disabled={cancelingId === job.id}
                        className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 font-medium text-amber-700 disabled:opacity-60"
                      >
                        {cancelingId === job.id ? "Canceling..." : "Cancel"}
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
