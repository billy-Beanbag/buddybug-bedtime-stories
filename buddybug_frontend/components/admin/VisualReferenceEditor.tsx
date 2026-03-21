"use client";

import { useEffect, useState } from "react";

import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { VisualReferenceAssetRead } from "@/lib/types";

export function VisualReferenceEditor({
  asset,
  characterOptions,
  submitting,
  onSubmit,
  onClear,
}: {
  asset: VisualReferenceAssetRead | null;
  characterOptions: Array<{ id: number; name: string }>;
  submitting: boolean;
  onSubmit: (payload: Record<string, unknown>, assetId?: number) => Promise<void>;
  onClear: () => void;
}) {
  const [name, setName] = useState("");
  const [referenceType, setReferenceType] = useState("character_sheet");
  const [targetType, setTargetType] = useState("");
  const [targetId, setTargetId] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [promptNotes, setPromptNotes] = useState("");
  const [language, setLanguage] = useState("");
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    setName(asset?.name || "");
    setReferenceType(asset?.reference_type || "character_sheet");
    setTargetType(asset?.target_type || "");
    setTargetId(asset?.target_id ? String(asset.target_id) : "");
    setImageUrl(asset?.image_url || "");
    setPromptNotes(asset?.prompt_notes || "");
    setLanguage(asset?.language || "");
    setIsActive(asset?.is_active ?? true);
  }, [asset]);

  const payload = {
    name,
    reference_type: referenceType,
    target_type: targetType || null,
    target_id: targetType && targetId ? Number(targetId) : null,
    image_url: imageUrl,
    prompt_notes: promptNotes || null,
    language: language || null,
    is_active: isActive,
  };

  return (
    <form
      className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(payload, asset?.id);
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{asset ? "Edit visual reference" : "Add visual reference"}</h2>
          <p className="mt-1 text-sm text-slate-600">
            Track reusable image references and prompt notes for characters, books, lanes, drafts, or editorial projects.
            Use `/artwork-assets/...` for files stored in the repo `Artwork` folder.
          </p>
        </div>
        {asset ? (
          <button
            type="button"
            onClick={onClear}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900"
          >
            New asset
          </button>
        ) : null}
      </div>

      <div className="mt-4 grid gap-4">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Name</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="Buddybug character sheet"
            required
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Reference type</span>
            <select
              value={referenceType}
              onChange={(event) => setReferenceType(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            >
              <option value="character_sheet">character_sheet</option>
              <option value="style_reference">style_reference</option>
              <option value="cover_reference">cover_reference</option>
              <option value="scene_reference">scene_reference</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Language</span>
            <input
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
              placeholder="en"
            />
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Target type</span>
            <select
              value={targetType}
              onChange={(event) => setTargetType(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            >
              <option value="">Global</option>
              <option value="character">character</option>
              <option value="content_lane">content_lane</option>
              <option value="editorial_project">editorial_project</option>
              <option value="book">book</option>
              <option value="story_draft">story_draft</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Target ID</span>
            {targetType === "character" ? (
              <select
                value={targetId}
                onChange={(event) => setTargetId(event.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
              >
                <option value="">Select a character</option>
                {characterOptions.map((character) => (
                  <option key={character.id} value={character.id}>
                    {character.name} #{character.id}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="number"
                min={1}
                value={targetId}
                onChange={(event) => setTargetId(event.target.value)}
                disabled={!targetType}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 disabled:bg-slate-50"
                placeholder={targetType ? "Required for targeted assets" : "Select a target type first"}
              />
            )}
          </label>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Image URL</span>
          <input
            value={imageUrl}
            onChange={(event) => setImageUrl(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="/artwork-assets/Buddybug-main.png"
            required
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Prompt notes</span>
          <textarea
            value={promptNotes}
            onChange={(event) => setPromptNotes(event.target.value)}
            rows={5}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="Keep the moonlit watercolor palette, rounded eyes, and Buddybug's scarf shape consistent."
          />
        </label>

        <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
          <input type="checkbox" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />
          Asset is active and should appear in reference lookups
        </label>
      </div>

      <button
        type="submit"
        disabled={submitting || !name.trim() || !imageUrl.trim() || (!!targetType && !targetId)}
        className={`mt-4 rounded-2xl px-5 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
      >
        {submitting ? "Saving..." : asset ? "Save asset" : "Create asset"}
      </button>
    </form>
  );
}
