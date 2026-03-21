"use client";

import type { MaintenanceJobRead } from "@/lib/types";

function prettyJson(value: string | null) {
  if (!value) {
    return null;
  }
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}

export function MaintenanceJobDetail({
  job,
  running,
  canceling,
  onRun,
  onCancel,
}: {
  job: MaintenanceJobRead | null;
  running?: boolean;
  canceling?: boolean;
  onRun: (job: MaintenanceJobRead) => Promise<void>;
  onCancel: (job: MaintenanceJobRead) => Promise<void>;
}) {
  if (!job) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Job detail</h3>
        <p className="mt-3 text-sm text-slate-600">Select a maintenance job to inspect its scope, status, result, and any failure details.</p>
      </section>
    );
  }

  const formattedParameters = prettyJson(job.parameters_json);
  const formattedResult = prettyJson(job.result_json);

  return (
    <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">
            Maintenance job #{job.id} • {job.key}
          </p>
          <h3 className="mt-1 text-xl font-semibold text-slate-900">{job.title}</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{job.status}</span>
          <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">{job.job_type}</span>
        </div>
      </div>

      <div className="grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
        <div>
          <p className="font-medium text-slate-900">Target scope</p>
          <p>{job.target_scope || "all"}</p>
        </div>
        <div>
          <p className="font-medium text-slate-900">Created by</p>
          <p>{job.created_by_user_id ? `Admin #${job.created_by_user_id}` : "System"}</p>
        </div>
        <div>
          <p className="font-medium text-slate-900">Started</p>
          <p>{job.started_at ? new Date(job.started_at).toLocaleString() : "Not started"}</p>
        </div>
        <div>
          <p className="font-medium text-slate-900">Completed</p>
          <p>{job.completed_at ? new Date(job.completed_at).toLocaleString() : "Not completed"}</p>
        </div>
      </div>

      {job.description ? (
        <div>
          <p className="text-sm font-medium text-slate-900">Description</p>
          <p className="mt-1 text-sm text-slate-700">{job.description}</p>
        </div>
      ) : null}

      {formattedParameters ? (
        <div>
          <p className="text-sm font-medium text-slate-900">Parameters JSON</p>
          <pre className="mt-2 overflow-x-auto rounded-2xl bg-slate-50 px-4 py-3 text-xs text-slate-700">{formattedParameters}</pre>
        </div>
      ) : null}

      {formattedResult ? (
        <div>
          <p className="text-sm font-medium text-slate-900">Result JSON</p>
          <pre className="mt-2 overflow-x-auto rounded-2xl bg-emerald-50 px-4 py-3 text-xs text-emerald-900">{formattedResult}</pre>
        </div>
      ) : null}

      {job.error_message ? (
        <div>
          <p className="text-sm font-medium text-rose-700">Error</p>
          <pre className="mt-2 overflow-x-auto rounded-2xl bg-rose-50 px-4 py-3 text-xs text-rose-900">{job.error_message}</pre>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3">
        {job.status === "pending" || job.status === "failed" ? (
          <button
            type="button"
            onClick={() => void onRun(job)}
            disabled={running}
            className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700 disabled:opacity-60"
          >
            {running ? "Running..." : "Run job"}
          </button>
        ) : null}
        {job.status === "pending" ? (
          <button
            type="button"
            onClick={() => void onCancel(job)}
            disabled={canceling}
            className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-700 disabled:opacity-60"
          >
            {canceling ? "Canceling..." : "Cancel job"}
          </button>
        ) : null}
      </div>
    </section>
  );
}
