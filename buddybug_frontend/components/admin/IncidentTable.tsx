"use client";

import Link from "next/link";

import type { IncidentRecordRead } from "@/lib/types";

function severityClasses(severity: string) {
  if (severity === "sev_1") {
    return "bg-rose-100 text-rose-700";
  }
  if (severity === "sev_2") {
    return "bg-amber-100 text-amber-700";
  }
  if (severity === "sev_3") {
    return "bg-sky-100 text-sky-700";
  }
  return "bg-slate-100 text-slate-700";
}

export function IncidentTable({ incidents }: { incidents: IncidentRecordRead[] }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Incident</th>
              <th className="px-4 py-3 font-medium">Severity</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Area</th>
              <th className="px-4 py-3 font-medium">Assignee</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {incidents.map((incident) => (
              <tr key={incident.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{incident.title}</div>
                  <p className="mt-1 max-w-lg text-slate-600">{incident.summary}</p>
                  <div className="mt-2 text-xs text-slate-500">
                    #{incident.id}
                    {incident.feature_flag_key ? ` • flag ${incident.feature_flag_key}` : ""}
                  </div>
                </td>
                <td className="px-4 py-4 align-top">
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${severityClasses(incident.severity)}`}>
                    {incident.severity}
                  </span>
                </td>
                <td className="px-4 py-4 align-top">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{incident.status}</span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{incident.affected_area}</td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {incident.assigned_to_user_id ? `Admin #${incident.assigned_to_user_id}` : "Unassigned"}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{new Date(incident.updated_at).toLocaleString()}</td>
                <td className="px-4 py-4 align-top">
                  <Link
                    href={`/admin/incidents/${incident.id}`}
                    className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                  >
                    Open incident
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
