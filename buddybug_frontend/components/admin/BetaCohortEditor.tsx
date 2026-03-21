"use client";

import { useEffect, useState } from "react";

import type { BetaCohortRead } from "@/lib/types";

export interface BetaCohortFormValue {
  key: string;
  name: string;
  description: string;
  is_active: boolean;
  feature_flag_keys: string;
  notes: string;
}

const EMPTY_FORM: BetaCohortFormValue = {
  key: "",
  name: "",
  description: "",
  is_active: true,
  feature_flag_keys: "",
  notes: "",
};

function toFormValue(cohort?: BetaCohortRead | null): BetaCohortFormValue {
  if (!cohort) {
    return EMPTY_FORM;
  }
  return {
    key: cohort.key,
    name: cohort.name,
    description: cohort.description || "",
    is_active: cohort.is_active,
    feature_flag_keys: cohort.feature_flag_keys || "",
    notes: cohort.notes || "",
  };
}

export function BetaCohortEditor({
  cohort,
  submitting = false,
  onSubmit,
  onCancel,
}: {
  cohort?: BetaCohortRead | null;
  submitting?: boolean;
  onSubmit: (value: BetaCohortFormValue) => Promise<void>;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState<BetaCohortFormValue>(() => toFormValue(cohort));

  useEffect(() => {
    setForm(toFormValue(cohort));
  }, [cohort]);

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(form);
      }}
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{cohort ? "Edit beta cohort" : "Create beta cohort"}</h2>
        <p className="mt-1 text-sm text-slate-600">Keep cohorts small and purpose-driven so early access rules stay easy to explain.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Key</span>
          <input
            value={form.key}
            onChange={(event) => setForm((current) => ({ ...current, key: event.target.value }))}
            placeholder="offline_sync_beta"
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900"
            disabled={submitting || Boolean(cohort)}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Name</span>
          <input
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            placeholder="Offline sync beta"
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Description</span>
        <textarea
          value={form.description}
          onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
          rows={3}
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900"
          disabled={submitting}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Linked feature flag keys</span>
        <input
          value={form.feature_flag_keys}
          onChange={(event) => setForm((current) => ({ ...current, feature_flag_keys: event.target.value }))}
          placeholder="offline_downloads_enabled"
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900"
          disabled={submitting}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Notes</span>
        <textarea
          value={form.notes}
          onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
          rows={3}
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900"
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
        Cohort is active
      </label>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={submitting || !form.key.trim() || !form.name.trim()}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Saving..." : cohort ? "Save changes" : "Create cohort"}
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
