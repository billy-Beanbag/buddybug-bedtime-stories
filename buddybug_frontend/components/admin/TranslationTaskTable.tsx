"use client";

import type { TranslationTaskDetailResponse } from "@/lib/types";

export function TranslationTaskTable({
  items,
  selectedTaskId,
  onSelect,
}: {
  items: TranslationTaskDetailResponse[];
  selectedTaskId: number | null;
  onSelect: (item: TranslationTaskDetailResponse) => void;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Book</th>
              <th className="px-4 py-3 font-medium">Language</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Coverage</th>
              <th className="px-4 py-3 font-medium">Assignee</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.task?.id ?? `${item.book_id}-${item.target_language}`} className={selectedTaskId === item.task?.id ? "bg-indigo-50/50" : ""}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{item.book_title}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    Book #{item.book_id} • {item.age_band}
                  </div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div className="font-medium text-slate-900">{item.target_language.toUpperCase()}</div>
                  <div className="mt-1 text-xs text-slate-500">Source {item.source_language.toUpperCase()}</div>
                </td>
                <td className="px-4 py-4 align-top">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      item.task?.status === "completed"
                        ? "bg-emerald-100 text-emerald-700"
                        : item.task?.status === "blocked"
                          ? "bg-rose-100 text-rose-700"
                          : "bg-amber-100 text-amber-700"
                    }`}
                  >
                    {item.task?.status || "missing"}
                  </span>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div>
                    {item.translated_page_count}/{item.total_page_count} pages
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {item.has_book_translation ? "Metadata ready" : "Metadata missing"} •{" "}
                    {item.is_translation_published ? "Published" : "Internal only"}
                  </div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  {item.task?.assigned_to_user_id ? `User #${item.task.assigned_to_user_id}` : "Unassigned"}
                </td>
                <td className="px-4 py-4 align-top">
                  <button
                    type="button"
                    onClick={() => onSelect(item)}
                    className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                  >
                    {item.task ? "Edit task" : "Create task"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
