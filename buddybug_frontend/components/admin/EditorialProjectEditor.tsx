"use client";

import { useEffect, useState } from "react";

import type { EditorialProjectRead } from "@/lib/types";

export function EditorialProjectEditor({
  project,
  onSave,
  onReadyForPublish,
  onPublish,
}: {
  project: EditorialProjectRead;
  onSave: (payload: Partial<EditorialProjectRead>) => Promise<void>;
  onReadyForPublish: () => Promise<void>;
  onPublish: () => Promise<void>;
}) {
  const [form, setForm] = useState({
    title: project.title,
    slug: project.slug,
    description: project.description || "",
    age_band: project.age_band,
    content_lane_key: project.content_lane_key || "",
    language: project.language,
    status: project.status,
    source_type: project.source_type,
    notes: project.notes || "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm({
      title: project.title,
      slug: project.slug,
      description: project.description || "",
      age_band: project.age_band,
      content_lane_key: project.content_lane_key || "",
      language: project.language,
      status: project.status,
      source_type: project.source_type,
      notes: project.notes || "",
    });
  }, [project]);

  return (
    <div className="space-y-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Project metadata</h3>
        <p className="mt-1 text-sm text-slate-600">Update editorial status, language, and publishing notes.</p>
      </div>

      <div className="grid gap-3">
        <input
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
        <input
          value={form.slug}
          onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
        <textarea
          value={form.description}
          onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
          rows={3}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          placeholder="Project description"
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
          <select
            value={form.source_type}
            onChange={(event) => setForm((current) => ({ ...current, source_type: event.target.value }))}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            <option value="manual">manual</option>
            <option value="mixed">mixed</option>
            <option value="ai_generated">ai_generated</option>
          </select>
        </div>
        <input
          value={form.content_lane_key}
          onChange={(event) => setForm((current) => ({ ...current, content_lane_key: event.target.value }))}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          placeholder="content lane key"
        />
        <textarea
          value={form.notes}
          onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
          rows={4}
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          placeholder="Editorial notes"
        />
      </div>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() =>
            void onSave({
              ...form,
              description: form.description || null,
              content_lane_key: form.content_lane_key || null,
              notes: form.notes || null,
            })
              .then(() => {
                setMessage("Project updated.");
                setError(null);
              })
              .catch((err) => {
                setError(err instanceof Error ? err.message : "Unable to update project");
                setMessage(null);
              })
          }
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
        >
          Save project
        </button>
        <button
          type="button"
          onClick={() =>
            void onReadyForPublish()
              .then(() => {
                setMessage("Project marked ready for publish.");
                setError(null);
              })
              .catch((err) => {
                setError(err instanceof Error ? err.message : "Unable to mark ready for publish");
                setMessage(null);
              })
          }
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Ready for publish
        </button>
        <button
          type="button"
          onClick={() =>
            void onPublish()
              .then(() => {
                setMessage("Project published.");
                setError(null);
              })
              .catch((err) => {
                setError(err instanceof Error ? err.message : "Unable to publish project");
                setMessage(null);
              })
          }
          className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800"
        >
          Publish
        </button>
      </div>
    </div>
  );
}
