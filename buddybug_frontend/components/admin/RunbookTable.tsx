"use client";

import type { RunbookEntryRead } from "@/lib/types";

export function RunbookTable({
  runbooks,
  savingId,
  onEdit,
  onDeactivate,
}: {
  runbooks: RunbookEntryRead[];
  savingId: number | null;
  onEdit: (runbook: RunbookEntryRead) => void;
  onDeactivate: (runbook: RunbookEntryRead) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Runbook</th>
              <th className="px-4 py-3 font-medium">Area</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {runbooks.map((runbook) => (
              <tr key={runbook.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{runbook.title}</div>
                  <div className="mt-1 text-xs text-slate-500">{runbook.key}</div>
                  <p className="mt-2 max-w-xl text-slate-600">{runbook.summary}</p>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{runbook.area}</td>
                <td className="px-4 py-4 align-top">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${runbook.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
                    {runbook.is_active ? "active" : "inactive"}
                  </span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{new Date(runbook.updated_at).toLocaleString()}</td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onEdit(runbook)}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                    >
                      Edit
                    </button>
                    {runbook.is_active ? (
                      <button
                        type="button"
                        onClick={() => void onDeactivate(runbook)}
                        disabled={savingId === runbook.id}
                        className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 font-medium text-amber-700 disabled:opacity-60"
                      >
                        {savingId === runbook.id ? "Deactivating..." : "Deactivate"}
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
