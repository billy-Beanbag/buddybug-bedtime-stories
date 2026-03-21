"use client";

import Link from "next/link";

import type { BetaCohortRead } from "@/lib/types";

export function BetaCohortTable({
  cohorts,
  onEdit,
}: {
  cohorts: BetaCohortRead[];
  onEdit: (cohort: BetaCohortRead) => void;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Cohort</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Feature flags</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {cohorts.map((cohort) => (
              <tr key={cohort.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{cohort.name}</div>
                  <div className="mt-1 font-mono text-xs text-slate-500">{cohort.key}</div>
                  {cohort.description ? <p className="mt-2 max-w-xl text-slate-600">{cohort.description}</p> : null}
                </td>
                <td className="px-4 py-4 align-top">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${cohort.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700"}`}>
                    {cohort.is_active ? "active" : "inactive"}
                  </span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{cohort.feature_flag_keys || "Mapped in service or later"}</td>
                <td className="px-4 py-4 align-top text-slate-700">{new Date(cohort.updated_at).toLocaleString()}</td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <Link
                      href={`/admin/beta/${cohort.id}`}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                    >
                      View members
                    </Link>
                    <button
                      type="button"
                      onClick={() => onEdit(cohort)}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                    >
                      Edit
                    </button>
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
