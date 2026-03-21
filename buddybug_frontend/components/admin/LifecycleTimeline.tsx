import type { LifecycleMilestoneRead } from "@/lib/types";

function formatMilestoneLabel(value: string) {
  return value.replaceAll("_", " ");
}

export function LifecycleTimeline({ milestones }: { milestones: LifecycleMilestoneRead[] }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <p className="text-sm text-slate-500">Unified account journey</p>
        <h2 className="mt-1 text-2xl font-semibold text-slate-900">Timeline</h2>
      </div>
      {milestones.length ? (
        <div className="mt-5 space-y-4">
          {milestones.map((milestone) => (
            <article key={milestone.id} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{milestone.title}</h3>
                  <p className="mt-1 text-xs uppercase tracking-[0.12em] text-slate-500">
                    {formatMilestoneLabel(milestone.milestone_type)}
                  </p>
                </div>
                <div className="text-right text-xs text-slate-500">
                  <div>{new Date(milestone.occurred_at).toLocaleString()}</div>
                  <div className="mt-1">
                    {milestone.source_table || "derived"}
                    {milestone.source_id ? ` • ${milestone.source_id}` : ""}
                  </div>
                </div>
              </div>
              {milestone.summary ? <p className="mt-3 text-sm leading-6 text-slate-700">{milestone.summary}</p> : null}
            </article>
          ))}
        </div>
      ) : (
        <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
          No lifecycle milestones have been built for this user yet.
        </div>
      )}
    </section>
  );
}
