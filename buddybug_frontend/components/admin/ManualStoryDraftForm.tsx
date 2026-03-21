"use client";

import { useEffect, useState } from "react";

import type { EditorialStoryDraftRead } from "@/lib/types";

export function ManualStoryDraftForm({
  draft,
  projectId,
  projectAgeBand,
  projectLanguage,
  onCreate,
  onSave,
}: {
  draft: EditorialStoryDraftRead | null;
  projectId: number;
  projectAgeBand: string;
  projectLanguage: string;
  onCreate: (payload: {
    title: string;
    full_text: string;
    summary: string;
    age_band: string;
    language: string;
    project_id: number;
    review_status: string;
    read_time_minutes: number;
  }) => Promise<void>;
  onSave: (payload: Record<string, unknown>) => Promise<void>;
}) {
  const [form, setForm] = useState({
    title: draft?.title || "",
    full_text: draft?.full_text || "",
    summary: draft?.summary || "",
    age_band: draft?.age_band || projectAgeBand,
    language: draft?.language || projectLanguage,
    review_status: draft?.review_status || "draft_pending_review",
    read_time_minutes: draft?.read_time_minutes || 5,
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm({
      title: draft?.title || "",
      full_text: draft?.full_text || "",
      summary: draft?.summary || "",
      age_band: draft?.age_band || projectAgeBand,
      language: draft?.language || projectLanguage,
      review_status: draft?.review_status || "draft_pending_review",
      read_time_minutes: draft?.read_time_minutes || 5,
    });
  }, [draft, projectAgeBand, projectLanguage]);

  return (
    <div className="space-y-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Manual draft</h3>
        <p className="mt-1 text-sm text-slate-600">Write or refine the story text directly.</p>
      </div>
      <input
        value={form.title}
        onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
        placeholder="Draft title"
        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
      />
      <textarea
        value={form.summary}
        onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))}
        rows={3}
        placeholder="Summary"
        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
      />
      <textarea
        value={form.full_text}
        onChange={(event) => setForm((current) => ({ ...current, full_text: event.target.value }))}
        rows={8}
        placeholder="Full story text"
        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
      />
      <div className="grid gap-3 sm:grid-cols-3">
        <select
          value={form.age_band}
          onChange={(event) => setForm((current) => ({ ...current, age_band: event.target.value }))}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        >
          <option value="3-7">3-7</option>
          <option value="8-12">8-12</option>
        </select>
        <input
          value={form.language}
          onChange={(event) => setForm((current) => ({ ...current, language: event.target.value }))}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
        <input
          type="number"
          value={form.read_time_minutes}
          onChange={(event) =>
            setForm((current) => ({ ...current, read_time_minutes: Number(event.target.value || 0) }))
          }
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
      </div>
      <select
        value={form.review_status}
        onChange={(event) => setForm((current) => ({ ...current, review_status: event.target.value }))}
        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
      >
        <option value="draft_pending_review">draft_pending_review</option>
        <option value="needs_revision">needs_revision</option>
        <option value="approved_for_illustration">approved_for_illustration</option>
      </select>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <button
        type="button"
        onClick={() => {
          const action = draft
            ? onSave(form)
            : onCreate({
                ...form,
                project_id: projectId,
              });
          void action.catch((err) => setError(err instanceof Error ? err.message : "Unable to save draft"));
        }}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
      >
        {draft ? "Save draft" : "Create draft"}
      </button>
    </div>
  );
}
