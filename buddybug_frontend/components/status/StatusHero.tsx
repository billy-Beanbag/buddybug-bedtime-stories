import type { PublicStatusPageResponse } from "@/lib/types";

const STATUS_STYLES: Record<string, string> = {
  operational: "bg-emerald-50 text-emerald-700 border-emerald-200",
  degraded_performance: "bg-amber-50 text-amber-700 border-amber-200",
  partial_outage: "bg-orange-50 text-orange-700 border-orange-200",
  major_outage: "bg-rose-50 text-rose-700 border-rose-200",
  maintenance: "bg-sky-50 text-sky-700 border-sky-200",
};

function formatStatusLabel(value: string) {
  return value.replaceAll("_", " ");
}

export function StatusHero({ overallStatus }: { overallStatus: PublicStatusPageResponse["overall_status"] }) {
  return (
    <section className="rounded-[2.5rem] border border-white/70 bg-white/85 p-8 shadow-sm md:p-10">
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">Service Status</p>
      <div className="mt-4 flex flex-wrap items-center gap-4">
        <h1 className="text-4xl font-semibold tracking-tight text-slate-900">Buddybug system status</h1>
        <span className={`rounded-full border px-4 py-2 text-sm font-semibold ${STATUS_STYLES[overallStatus] || STATUS_STYLES.operational}`}>
          {formatStatusLabel(overallStatus)}
        </span>
      </div>
      <p className="mt-4 max-w-3xl text-base leading-7 text-slate-600">
        This page shares customer-safe updates about reading, narrated stories, billing, and account access. Internal engineering details stay private while active customer impact is communicated here.
      </p>
    </section>
  );
}
