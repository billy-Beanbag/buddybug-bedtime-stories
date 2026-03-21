import type { MarketingFaqItem } from "@/lib/marketing-content";

export function FAQSection({ items }: { items: MarketingFaqItem[] }) {
  return (
    <section className="space-y-5">
      <div>
        <h2 className="text-3xl font-semibold tracking-tight text-slate-900">Frequently asked questions</h2>
        <p className="mt-2 text-base leading-7 text-slate-600">
          Clear answers for parents evaluating Buddybug for real family use.
        </p>
      </div>
      <div className="grid gap-4">
        {items.map((item) => (
          <div key={item.question} className="rounded-3xl border border-white/70 bg-white/85 p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">{item.question}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.answer}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
