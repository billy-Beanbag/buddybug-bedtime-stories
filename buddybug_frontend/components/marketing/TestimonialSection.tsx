import type { MarketingTestimonial } from "@/lib/marketing-content";

export function TestimonialSection({
  items,
  title = "Parents already want this feeling",
}: {
  items: MarketingTestimonial[];
  title?: string;
}) {
  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-3xl font-semibold tracking-tight text-slate-900">{title}</h2>
        <p className="mt-2 text-base leading-7 text-slate-600">
          Placeholder social proof that can be replaced with real launch feedback later.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {items.map((item) => (
          <div key={item.quote} className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-sm">
            <p className="text-base leading-7 text-slate-700">“{item.quote}”</p>
            <p className="mt-4 text-sm font-semibold text-slate-900">{item.name}</p>
            <p className="text-sm text-slate-500">{item.context}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
