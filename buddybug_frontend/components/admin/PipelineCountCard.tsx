import { ADMIN_CARD_HOVER } from "@/lib/admin-styles";

export function PipelineCountCard({
  label,
  count,
}: {
  label: string;
  count: number;
}) {
  return (
    <div className={`rounded-3xl border border-slate-200 bg-white p-5 shadow-sm ${ADMIN_CARD_HOVER}`}>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-slate-900">{count}</p>
    </div>
  );
}
