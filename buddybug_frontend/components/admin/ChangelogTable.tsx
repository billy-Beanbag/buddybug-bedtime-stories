"use client";

import type { ChangelogEntryRead } from "@/lib/types";

function splitCsv(value: string | null) {
  return (value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function ChangelogTable({
  entries,
  publishingId,
  archivingId,
  onEdit,
  onPublish,
  onArchive,
}: {
  entries: ChangelogEntryRead[];
  publishingId: number | null;
  archivingId: number | null;
  onEdit: (entry: ChangelogEntryRead) => void;
  onPublish: (entry: ChangelogEntryRead) => Promise<void>;
  onArchive: (entry: ChangelogEntryRead) => Promise<void>;
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Release</th>
              <th className="px-4 py-3 font-medium">Audience</th>
              <th className="px-4 py-3 font-medium">Tags</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Updated</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td className="px-4 py-4 align-top">
                  <div className="font-medium text-slate-900">{entry.title}</div>
                  <div className="mt-1 text-xs text-slate-500">{entry.version_label}</div>
                  <p className="mt-2 max-w-xl text-slate-600">{entry.summary}</p>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{entry.audience}</td>
                <td className="px-4 py-4 align-top">
                  <div className="flex max-w-xs flex-wrap gap-2">
                    {splitCsv(entry.area_tags).map((tag) => (
                      <span key={`area-${entry.id}-${tag}`} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                        {tag}
                      </span>
                    ))}
                    {splitCsv(entry.feature_flag_keys).map((flagKey) => (
                      <span
                        key={`flag-${entry.id}-${flagKey}`}
                        className="rounded-full bg-indigo-50 px-2 py-1 text-xs text-indigo-700"
                      >
                        {flagKey}
                      </span>
                    ))}
                    {!splitCsv(entry.area_tags).length && !splitCsv(entry.feature_flag_keys).length ? (
                      <span className="text-xs text-slate-500">No tags</span>
                    ) : null}
                  </div>
                </td>
                <td className="px-4 py-4 align-top">
                  <div className="text-slate-700">{entry.status}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {entry.published_at ? `Published ${new Date(entry.published_at).toLocaleDateString()}` : "Not yet published"}
                  </div>
                </td>
                <td className="px-4 py-4 align-top text-slate-700">{new Date(entry.updated_at).toLocaleString()}</td>
                <td className="px-4 py-4 align-top">
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => onEdit(entry)}
                      className="rounded-2xl border border-slate-200 bg-white px-3 py-2 font-medium text-slate-900"
                    >
                      Edit
                    </button>
                    {entry.status !== "published" ? (
                      <button
                        type="button"
                        onClick={() => void onPublish(entry)}
                        disabled={publishingId === entry.id}
                        className="rounded-2xl border border-emerald-200 bg-emerald-50 px-3 py-2 font-medium text-emerald-700 disabled:opacity-60"
                      >
                        {publishingId === entry.id ? "Publishing..." : "Publish"}
                      </button>
                    ) : null}
                    {entry.status !== "archived" ? (
                      <button
                        type="button"
                        onClick={() => void onArchive(entry)}
                        disabled={archivingId === entry.id}
                        className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 font-medium text-amber-700 disabled:opacity-60"
                      >
                        {archivingId === entry.id ? "Archiving..." : "Archive"}
                      </button>
                    ) : null}
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
