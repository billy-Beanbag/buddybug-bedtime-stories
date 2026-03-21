import type { PublicStatusComponentRead } from "@/lib/types";

const STATUS_STYLES: Record<string, string> = {
  operational: "bg-emerald-50 text-emerald-700",
  degraded_performance: "bg-amber-50 text-amber-700",
  partial_outage: "bg-orange-50 text-orange-700",
  major_outage: "bg-rose-50 text-rose-700",
  maintenance: "bg-sky-50 text-sky-700",
};

function formatStatusLabel(value: string) {
  return value.replaceAll("_", " ");
}

export function StatusComponentList({ components }: { components: PublicStatusComponentRead[] }) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Customer-facing components</h2>
        <p className="mt-2 text-sm text-slate-600">A small set of public service areas with intentionally simple health labels.</p>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {components.map((component) => (
          <article key={component.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">{component.name}</h3>
                <p className="mt-1 text-sm text-slate-600">{component.description || "No public description provided."}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[component.current_status] || STATUS_STYLES.operational}`}>
                {formatStatusLabel(component.current_status)}
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
