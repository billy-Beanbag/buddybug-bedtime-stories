import type { SegmentBreakdownItem } from "@/lib/types";

export function BreakdownList({
  title,
  items,
}: {
  title: string;
  items: SegmentBreakdownItem[];
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
      <div className="mt-4 grid gap-2">
        {items.map((item) => (
          <div key={item.key} className="flex items-center justify-between rounded-2xl bg-slate-50 px-3 py-2 text-sm">
            <span className="text-slate-700">{item.key}</span>
            <span className="font-medium text-slate-900">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
