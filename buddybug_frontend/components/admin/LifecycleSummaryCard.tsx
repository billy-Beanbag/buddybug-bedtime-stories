import type { LifecycleSummaryResponse } from "@/lib/types";

export function LifecycleSummaryCard({ summary }: { summary: LifecycleSummaryResponse }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">Lifecycle summary</p>
          <h2 className="mt-1 text-2xl font-semibold text-slate-900">User #{summary.user_id}</h2>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
          {summary.lifecycle_stage || "unknown"}
        </span>
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-slate-500">First seen</div>
          <div className="mt-1 font-medium text-slate-900">
            {summary.first_seen_at ? new Date(summary.first_seen_at).toLocaleString() : "Unknown"}
          </div>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-slate-500">Latest activity</div>
          <div className="mt-1 font-medium text-slate-900">
            {summary.latest_activity_at ? new Date(summary.latest_activity_at).toLocaleString() : "Unknown"}
          </div>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-slate-500">Subscription</div>
          <div className="mt-1 font-medium text-slate-900">{summary.current_subscription_status || "unknown"}</div>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-slate-500">Support tickets</div>
          <div className="mt-1 font-medium text-slate-900">{summary.support_ticket_count}</div>
        </div>
      </div>
      <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 px-4 py-3 text-slate-700">
          Onboarding completed: {summary.has_completed_onboarding ? "Yes" : "No"}
        </div>
        <div className="rounded-2xl border border-slate-200 px-4 py-3 text-slate-700">
          Child profiles: {summary.has_child_profiles ? "Yes" : "No"}
        </div>
        <div className="rounded-2xl border border-slate-200 px-4 py-3 text-slate-700">
          Premium history: {summary.has_premium_history ? "Yes" : "No"}
        </div>
        <div className="rounded-2xl border border-slate-200 px-4 py-3 text-slate-700">
          Open billing recovery: {summary.open_billing_recovery ? "Yes" : "No"}
        </div>
      </div>
    </section>
  );
}
