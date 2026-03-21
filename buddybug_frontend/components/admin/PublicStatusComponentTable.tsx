"use client";

import type { PublicStatusComponentRead } from "@/lib/types";

const STATUS_OPTIONS = [
  "operational",
  "degraded_performance",
  "partial_outage",
  "major_outage",
  "maintenance",
] as const;

export function PublicStatusComponentTable({
  components,
  updatingComponentId,
  onUpdate,
}: {
  components: PublicStatusComponentRead[];
  updatingComponentId: number | null;
  onUpdate: (component: PublicStatusComponentRead, patch: Partial<PublicStatusComponentRead>) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Component</th>
              <th className="px-4 py-3 font-medium">Current status</th>
              <th className="px-4 py-3 font-medium">Visibility</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {components.map((component) => (
              <tr key={component.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{component.name}</div>
                  <div className="mt-1 text-xs text-slate-500">{component.key}</div>
                  {component.description ? <p className="mt-2 max-w-xl text-slate-600">{component.description}</p> : null}
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{component.current_status}</td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {component.is_active ? "Public component active" : "Hidden from public page"}
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    {STATUS_OPTIONS.map((statusValue) => (
                      <button
                        key={statusValue}
                        type="button"
                        onClick={() => void onUpdate(component, { current_status: statusValue })}
                        disabled={updatingComponentId === component.id || component.current_status === statusValue}
                        className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900 disabled:opacity-60"
                      >
                        {statusValue}
                      </button>
                    ))}
                    <button
                      type="button"
                      onClick={() => void onUpdate(component, { is_active: !component.is_active })}
                      disabled={updatingComponentId === component.id}
                      className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-900 disabled:opacity-60"
                    >
                      {component.is_active ? "Deactivate" : "Activate"}
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
