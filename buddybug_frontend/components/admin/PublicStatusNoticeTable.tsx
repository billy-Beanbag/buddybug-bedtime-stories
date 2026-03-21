"use client";

import type { PublicStatusNoticeRead } from "@/lib/types";

export function PublicStatusNoticeTable({
  notices,
  deletingNoticeId,
  onEdit,
  onDelete,
}: {
  notices: PublicStatusNoticeRead[];
  deletingNoticeId: number | null;
  onEdit: (notice: PublicStatusNoticeRead) => void;
  onDelete: (notice: PublicStatusNoticeRead) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Notice</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Timing</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {notices.map((notice) => (
              <tr key={notice.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{notice.title}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {notice.component_key || "all components"} • #{notice.id}
                  </div>
                  <p className="mt-2 max-w-xl text-slate-600">{notice.summary}</p>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{notice.notice_type}</td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div>{notice.public_status}</div>
                  <div className="mt-1 text-xs text-slate-500">{notice.is_public ? "public" : "hidden"} • {notice.is_active ? "active" : "inactive"}</div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">
                  <div>{new Date(notice.starts_at).toLocaleString()}</div>
                  <div className="mt-1 text-xs text-slate-500">{notice.ends_at ? `Ends ${new Date(notice.ends_at).toLocaleString()}` : "No end time"}</div>
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onEdit(notice)}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => void onDelete(notice)}
                      disabled={deletingNoticeId === notice.id}
                      className="rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 font-medium text-rose-700 disabled:opacity-60"
                    >
                      {deletingNoticeId === notice.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
