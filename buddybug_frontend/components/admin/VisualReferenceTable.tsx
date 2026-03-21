"use client";

import { resolveApiUrl } from "@/lib/api";
import type { VisualReferenceAssetRead } from "@/lib/types";

export function VisualReferenceTable({
  assets,
  deletingId,
  onEdit,
  onDelete,
}: {
  assets: VisualReferenceAssetRead[];
  deletingId: number | null;
  onEdit: (asset: VisualReferenceAssetRead) => void;
  onDelete: (asset: VisualReferenceAssetRead) => Promise<void>;
}) {
  return (
    <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Reference assets</h2>
        <p className="mt-1 text-sm text-slate-600">
          Reuse approved character sheets, style references, and prompt notes to keep recurring visuals steady.
        </p>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="py-3 pr-4 font-medium">Asset</th>
              <th className="py-3 pr-4 font-medium">Type</th>
              <th className="py-3 pr-4 font-medium">Target</th>
              <th className="py-3 pr-4 font-medium">Language</th>
              <th className="py-3 pr-4 font-medium">Status</th>
              <th className="py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {assets.map((asset) => (
              <tr key={asset.id} className="align-top text-slate-700">
                <td className="py-3 pr-4">
                  <div className="flex gap-3">
                    <div className="h-16 w-16 overflow-hidden rounded-2xl bg-slate-100">
                      <img src={resolveApiUrl(asset.image_url)} alt={asset.name} className="h-full w-full object-cover" />
                    </div>
                    <div>
                      <div className="font-medium text-slate-900">{asset.name}</div>
                      <div className="mt-1 text-xs text-slate-500">Created {new Date(asset.created_at).toLocaleDateString()}</div>
                      {asset.prompt_notes ? <div className="mt-2 max-w-md text-xs text-slate-600">{asset.prompt_notes}</div> : null}
                    </div>
                  </div>
                </td>
                <td className="py-3 pr-4">{asset.reference_type}</td>
                <td className="py-3 pr-4">
                  {asset.target_type ? `${asset.target_type} #${asset.target_id}` : "Global"}
                </td>
                <td className="py-3 pr-4">{asset.language || "All"}</td>
                <td className="py-3 pr-4">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      asset.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {asset.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="py-3">
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => onEdit(asset)}
                      className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      disabled={deletingId === asset.id}
                      onClick={() => void onDelete(asset)}
                      className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700 disabled:opacity-60"
                    >
                      {deletingId === asset.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
