"use client";

import { useEffect, useState } from "react";

import { ADMIN_PRIMARY_BUTTON, ADMIN_SECONDARY_BUTTON } from "@/lib/admin-styles";
import type { RunbookEntryRead } from "@/lib/types";

export interface RunbookFormValue {
  key: string;
  title: string;
  area: string;
  summary: string;
  steps_markdown: string;
  is_active: boolean;
}

const EMPTY_FORM: RunbookFormValue = {
  key: "",
  title: "",
  area: "",
  summary: "",
  steps_markdown: "",
  is_active: true,
};

function toForm(runbook?: RunbookEntryRead | null): RunbookFormValue {
  if (!runbook) {
    return EMPTY_FORM;
  }
  return {
    key: runbook.key,
    title: runbook.title,
    area: runbook.area,
    summary: runbook.summary,
    steps_markdown: runbook.steps_markdown,
    is_active: runbook.is_active,
  };
}

export function RunbookEditor({
  runbook,
  submitting,
  onSubmit,
  onCancel,
}: {
  runbook?: RunbookEntryRead | null;
  submitting?: boolean;
  onSubmit: (value: RunbookFormValue) => Promise<void>;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState<RunbookFormValue>(() => toForm(runbook));

  useEffect(() => {
    setForm(toForm(runbook));
  }, [runbook]);

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(form);
      }}
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{runbook ? "Edit runbook" : "Create runbook"}</h3>
        <p className="mt-1 text-sm text-slate-600">Capture reusable operational recovery steps for recurring issues and handoffs.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Key</span>
          <input
            value={form.key}
            onChange={(event) => setForm((current) => ({ ...current, key: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            placeholder="reader-outage-recovery"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Area</span>
          <input
            value={form.area}
            onChange={(event) => setForm((current) => ({ ...current, area: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            placeholder="reader"
            disabled={submitting}
          />
        </label>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Title</span>
        <input
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          placeholder="Reader outage recovery"
          disabled={submitting}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Summary</span>
        <textarea
          value={form.summary}
          onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))}
          rows={3}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          placeholder="What this runbook is for and when to use it"
          disabled={submitting}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Steps</span>
        <textarea
          value={form.steps_markdown}
          onChange={(event) => setForm((current) => ({ ...current, steps_markdown: event.target.value }))}
          rows={10}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-mono text-sm text-slate-900"
          placeholder={"1. Confirm the scope\n2. Roll back the bad deploy\n3. Validate recovery with support"}
          disabled={submitting}
        />
      </label>

      <label className="flex items-center gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
          disabled={submitting}
        />
        Active runbook
      </label>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={submitting || !form.key.trim() || !form.title.trim() || !form.area.trim() || !form.summary.trim() || !form.steps_markdown.trim()}
          className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
        >
          {submitting ? "Saving..." : runbook ? "Save changes" : "Create runbook"}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_SECONDARY_BUTTON}`}
          >
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}
