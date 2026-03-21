import type { SupportMetricsResponse } from "@/lib/types";

export function SupportMetricsCard({ metrics }: { metrics: SupportMetricsResponse }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">Support health</h3>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-slate-500">Open tickets</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{metrics.open_tickets}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-slate-500">In progress</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{metrics.in_progress_tickets}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-slate-500">Resolved in window</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{metrics.resolved_30d}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-slate-500">Avg resolution hours</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">
            {metrics.avg_resolution_hours !== null ? metrics.avg_resolution_hours : "N/A"}
          </p>
        </div>
      </div>
    </div>
  );
}
