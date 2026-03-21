"use client";

import { useEffect, useState } from "react";

import type { ChangelogEntryRead } from "@/lib/types";

export interface ChangelogFormValue {
  version_label: string;
  title: string;
  summary: string;
  details_markdown: string;
  audience: string;
  status: string;
  area_tags: string;
  feature_flag_keys: string;
}

const EMPTY_FORM: ChangelogFormValue = {
  version_label: "",
  title: "",
  summary: "",
  details_markdown: "",
  audience: "internal",
  status: "draft",
  area_tags: "",
  feature_flag_keys: "",
};

function toForm(entry?: ChangelogEntryRead | null): ChangelogFormValue {
  if (!entry) {
    return EMPTY_FORM;
  }
  return {
    version_label: entry.version_label,
    title: entry.title,
    summary: entry.summary,
    details_markdown: entry.details_markdown || "",
    audience: entry.audience,
    status: entry.status,
    area_tags: entry.area_tags || "",
    feature_flag_keys: entry.feature_flag_keys || "",
  };
}

export function ChangelogEditor({
  entry,
  submitting,
  onSubmit,
  onCancel,
}: {
  entry?: ChangelogEntryRead | null;
  submitting?: boolean;
  onSubmit: (value: ChangelogFormValue) => Promise<void>;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState<ChangelogFormValue>(() => toForm(entry));

  useEffect(() => {
    setForm(toForm(entry));
  }, [entry]);

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(form);
      }}
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{entry ? "Edit changelog entry" : "Create changelog entry"}</h3>
        <p className="mt-1 text-sm text-slate-600">
          Capture release notes for internal launches now and published user-facing updates later.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Version label</span>
          <input
            value={form.version_label}
            onChange={(event) => setForm((current) => ({ ...current, version_label: event.target.value }))}
            placeholder="2026.03.1"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Audience</span>
          <select
            value={form.audience}
            onChange={(event) => setForm((current) => ({ ...current, audience: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          >
            <option value="internal">internal</option>
            <option value="user_facing">user_facing</option>
          </select>
        </label>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Title</span>
        <input
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          placeholder="Growth and launch tooling update"
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={submitting}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Summary</span>
        <textarea
          value={form.summary}
          onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))}
          rows={3}
          placeholder="Short release summary for changelog lists."
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={submitting}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Details</span>
        <textarea
          value={form.details_markdown}
          onChange={(event) => setForm((current) => ({ ...current, details_markdown: event.target.value }))}
          rows={8}
          placeholder={"## Highlights\n- Added a new launch checklist\n- Cleaned up admin reporting"}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-mono text-sm text-slate-900"
          disabled={submitting}
        />
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Area tags</span>
          <input
            value={form.area_tags}
            onChange={(event) => setForm((current) => ({ ...current, area_tags: event.target.value }))}
            placeholder="growth, reporting, onboarding"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Feature flag keys</span>
          <input
            value={form.feature_flag_keys}
            onChange={(event) => setForm((current) => ({ ...current, feature_flag_keys: event.target.value }))}
            placeholder="onboarding_v2_enabled, winback_banner_enabled"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Status</span>
          <select
            value={form.status}
            onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          >
            <option value="draft">draft</option>
            <option value="published">published</option>
            <option value="archived">archived</option>
          </select>
        </label>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={submitting || !form.version_label.trim() || !form.title.trim() || !form.summary.trim()}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Saving..." : entry ? "Save changes" : "Create entry"}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
          >
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}
