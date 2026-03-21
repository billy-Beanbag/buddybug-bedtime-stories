import type { ContentPerformanceItem } from "@/lib/types";

export function ContentPerformanceTable({ items }: { items: ContentPerformanceItem[] }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Title</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Language</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Age band</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Opens</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Completions</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Replays</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Downloads</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600">Narration</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.book_id}>
                <td className="px-4 py-3 text-slate-900">{item.title}</td>
                <td className="px-4 py-3 text-slate-700">{item.language.toUpperCase()}</td>
                <td className="px-4 py-3 text-slate-700">{item.age_band}</td>
                <td className="px-4 py-3 text-slate-700">{item.opens}</td>
                <td className="px-4 py-3 text-slate-700">{item.completions}</td>
                <td className="px-4 py-3 text-slate-700">{item.replays}</td>
                <td className="px-4 py-3 text-slate-700">{item.downloads}</td>
                <td className="px-4 py-3 text-slate-700">{item.narration_starts}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
