"use client";

import { useState } from "react";

import type { EditorialAssetRead } from "@/lib/types";

export function EditorialAssetsPanel({
  projectId,
  assets,
  onCreate,
  onToggleActive,
}: {
  projectId: number;
  assets: EditorialAssetRead[];
  onCreate: (payload: Record<string, unknown>) => Promise<void>;
  onToggleActive: (asset: EditorialAssetRead) => Promise<void>;
}) {
  const [assetType, setAssetType] = useState("cover_image");
  const [fileUrl, setFileUrl] = useState("");
  const [pageNumber, setPageNumber] = useState<number | "">("");

  return (
    <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Editorial assets</h3>
        <p className="mt-1 text-sm text-slate-600">Add cover and page image overrides with direct URLs.</p>
      </div>

      <div className="space-y-3">
        {assets.map((asset) => (
          <div key={asset.id} className="rounded-2xl border border-slate-200 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-900">{asset.asset_type}</p>
                <p className="mt-1 break-all text-xs text-slate-600">{asset.file_url}</p>
              </div>
              <button
                type="button"
                onClick={() => void onToggleActive(asset)}
                className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-800"
              >
                {asset.is_active ? "Active asset" : "Set active"}
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {asset.page_number ? `Page ${asset.page_number}` : "Project-wide"} {asset.language ? `• ${asset.language}` : ""}
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-3 rounded-2xl border border-dashed border-slate-300 p-4">
        <select
          value={assetType}
          onChange={(event) => setAssetType(event.target.value)}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        >
          <option value="cover_image">cover_image</option>
          <option value="page_image">page_image</option>
          <option value="reference_image">reference_image</option>
          <option value="manuscript_file">manuscript_file</option>
        </select>
        {assetType === "page_image" ? (
          <input
            type="number"
            value={pageNumber}
            onChange={(event) => setPageNumber(event.target.value ? Number(event.target.value) : "")}
            placeholder="Page number"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        ) : null}
        <input
          value={fileUrl}
          onChange={(event) => setFileUrl(event.target.value)}
          placeholder="https://... or /mock-assets/..."
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
        <button
          type="button"
          onClick={() =>
            void onCreate({
              project_id: projectId,
              asset_type: assetType,
              file_url: fileUrl,
              page_number: assetType === "page_image" && pageNumber !== "" ? pageNumber : null,
              is_active: true,
            }).then(() => {
              setFileUrl("");
              setPageNumber("");
            })
          }
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
        >
          Add asset
        </button>
      </div>
    </div>
  );
}
