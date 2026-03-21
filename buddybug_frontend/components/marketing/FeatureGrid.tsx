import type { MarketingFeature } from "@/lib/marketing-content";

export function FeatureGrid({
  title,
  description,
  items,
}: {
  title: string;
  description?: string;
  items: MarketingFeature[];
}) {
  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-3xl font-semibold tracking-tight text-slate-900">{title}</h2>
        {description ? <p className="mt-2 max-w-3xl text-base leading-7 text-slate-600">{description}</p> : null}
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {items.map((item) => (
          <div key={item.title} className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-sm">
            <p className="text-sm font-medium uppercase tracking-[0.16em] text-indigo-700">{item.icon}</p>
            <h3 className="mt-3 text-lg font-semibold text-slate-900">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
