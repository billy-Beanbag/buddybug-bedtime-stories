"use client";

import { useState } from "react";

import type { EditorialStoryPageRead } from "@/lib/types";

export function ManualStoryPagesEditor({
  draftId,
  pages,
  onCreate,
  onSave,
}: {
  draftId: number;
  pages: EditorialStoryPageRead[];
  onCreate: (payload: Record<string, unknown>) => Promise<void>;
  onSave: (pageId: number, payload: Record<string, unknown>) => Promise<void>;
}) {
  const [newPageNumber, setNewPageNumber] = useState(pages.length + 1);
  const [newPageText, setNewPageText] = useState("");
  const [newSceneSummary, setNewSceneSummary] = useState("");
  const [newImageUrl, setNewImageUrl] = useState("");

  return (
    <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Story pages</h3>
        <p className="mt-1 text-sm text-slate-600">Add and revise the page-by-page editorial plan.</p>
      </div>

      <div className="space-y-3">
        {pages.map((page) => (
          <article key={page.id} className="rounded-2xl border border-slate-200 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-900">Page {page.page_number}</p>
              <button
                type="button"
                onClick={() =>
                  void onSave(page.id, {
                    page_text: page.page_text,
                    scene_summary: page.scene_summary,
                    location: page.location,
                    mood: page.mood,
                    characters_present: page.characters_present,
                    illustration_prompt: page.illustration_prompt,
                    image_url: page.image_url,
                  })
                }
                className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-800"
              >
                Save page
              </button>
            </div>
            <div className="mt-3 grid gap-3">
              <textarea
                defaultValue={page.page_text}
                rows={3}
                onBlur={(event) => {
                  page.page_text = event.target.value;
                }}
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              />
              <input
                defaultValue={page.scene_summary}
                onBlur={(event) => {
                  page.scene_summary = event.target.value;
                }}
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
              />
              <input
                defaultValue={page.image_url || ""}
                onBlur={(event) => {
                  page.image_url = event.target.value;
                }}
                className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
                placeholder="Image URL"
              />
            </div>
          </article>
        ))}
      </div>

      <div className="rounded-2xl border border-dashed border-slate-300 p-4">
        <p className="text-sm font-semibold text-slate-900">Add page</p>
        <div className="mt-3 grid gap-3">
          <input
            type="number"
            value={newPageNumber}
            onChange={(event) => setNewPageNumber(Number(event.target.value || 0))}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
          <textarea
            value={newPageText}
            onChange={(event) => setNewPageText(event.target.value)}
            rows={3}
            placeholder="Page text"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
          <input
            value={newSceneSummary}
            onChange={(event) => setNewSceneSummary(event.target.value)}
            placeholder="Scene summary"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
          <input
            value={newImageUrl}
            onChange={(event) => setNewImageUrl(event.target.value)}
            placeholder="Image URL"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
          <button
            type="button"
            onClick={() =>
              void onCreate({
                story_draft_id: draftId,
                page_number: newPageNumber,
                page_text: newPageText,
                scene_summary: newSceneSummary,
                location: "Editorial scene",
                mood: "calm",
                characters_present: "Buddybug",
                illustration_prompt: "",
                image_url: newImageUrl || null,
              }).then(() => {
                setNewPageNumber((current) => current + 1);
                setNewPageText("");
                setNewSceneSummary("");
                setNewImageUrl("");
              })
            }
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
          >
            Add page
          </button>
        </div>
      </div>
    </div>
  );
}
