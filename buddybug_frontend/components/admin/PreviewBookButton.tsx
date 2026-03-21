"use client";

import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { PreviewBookResponse } from "@/lib/types";

export function PreviewBookButton({
  label,
  onRun,
  preview,
}: {
  label: string;
  onRun: () => Promise<void>;
  preview: PreviewBookResponse | null;
}) {
  return (
    <div className="space-y-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <button
        type="button"
        onClick={() => void onRun()}
        className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
      >
        {label}
      </button>

      {preview ? (
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-900">{preview.book.title}</p>
          <p className="mt-1 text-xs text-slate-500">
            {preview.preview_only ? "Preview book" : "Published book"} • {preview.pages.length} pages
          </p>
          <div className="mt-3 space-y-2">
            {preview.pages.slice(0, 5).map((page) => (
              <div key={page.id} className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700">
                Page {page.page_number}: {page.text_content.slice(0, 100)}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
