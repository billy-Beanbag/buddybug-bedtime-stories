"use client";

import { useEffect, useState } from "react";

import type { PublicStatusComponentRead, PublicStatusNoticeRead } from "@/lib/types";

const STATUS_OPTIONS = [
  "operational",
  "degraded_performance",
  "partial_outage",
  "major_outage",
  "maintenance",
] as const;
const NOTICE_TYPES = ["incident", "maintenance", "informational"] as const;

export interface PublicStatusNoticeFormValue {
  title: string;
  summary: string;
  notice_type: string;
  public_status: string;
  component_key: string;
  linked_incident_id: string;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
  is_public: boolean;
}

const EMPTY_FORM: PublicStatusNoticeFormValue = {
  title: "",
  summary: "",
  notice_type: "incident",
  public_status: "degraded_performance",
  component_key: "",
  linked_incident_id: "",
  starts_at: "",
  ends_at: "",
  is_active: true,
  is_public: true,
};

function toDateInputValue(value: string | null) {
  if (!value) {
    return "";
  }
  return new Date(value).toISOString().slice(0, 16);
}

function toFormValue(notice?: PublicStatusNoticeRead | null): PublicStatusNoticeFormValue {
  if (!notice) {
    return EMPTY_FORM;
  }
  return {
    title: notice.title,
    summary: notice.summary,
    notice_type: notice.notice_type,
    public_status: notice.public_status,
    component_key: notice.component_key || "",
    linked_incident_id: notice.linked_incident_id ? String(notice.linked_incident_id) : "",
    starts_at: toDateInputValue(notice.starts_at),
    ends_at: toDateInputValue(notice.ends_at),
    is_active: notice.is_active,
    is_public: notice.is_public,
  };
}

export function PublicStatusNoticeEditor({
  components,
  notice,
  submitting = false,
  onSubmit,
  onCancel,
}: {
  components: PublicStatusComponentRead[];
  notice?: PublicStatusNoticeRead | null;
  submitting?: boolean;
  onSubmit: (value: PublicStatusNoticeFormValue) => Promise<void>;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState<PublicStatusNoticeFormValue>(() => toFormValue(notice));

  useEffect(() => {
    setForm(toFormValue(notice));
  }, [notice]);

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(form);
      }}
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{notice ? "Edit public notice" : "Create public notice"}</h2>
        <p className="mt-1 text-sm text-slate-600">Write customer-safe language only. Internal root cause and mitigation detail should stay in incident tooling.</p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Title</span>
        <input
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Summary</span>
        <textarea
          value={form.summary}
          onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))}
          rows={4}
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Notice type</span>
          <select
            value={form.notice_type}
            onChange={(event) => setForm((current) => ({ ...current, notice_type: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            {NOTICE_TYPES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Public status</span>
          <select
            value={form.public_status}
            onChange={(event) => setForm((current) => ({ ...current, public_status: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Component</span>
          <select
            value={form.component_key}
            onChange={(event) => setForm((current) => ({ ...current, component_key: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All components</option>
            {components.map((component) => (
              <option key={component.id} value={component.key}>
                {component.name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Linked incident ID</span>
          <input
            type="number"
            min={1}
            value={form.linked_incident_id}
            onChange={(event) => setForm((current) => ({ ...current, linked_incident_id: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Starts at</span>
          <input
            type="datetime-local"
            value={form.starts_at}
            onChange={(event) => setForm((current) => ({ ...current, starts_at: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Ends at</span>
          <input
            type="datetime-local"
            value={form.ends_at}
            onChange={(event) => setForm((current) => ({ ...current, ends_at: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        </label>
      </div>

      <label className="flex items-center gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
        />
        Notice is active
      </label>
      <label className="flex items-center gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.is_public}
          onChange={(event) => setForm((current) => ({ ...current, is_public: event.target.checked }))}
        />
        Notice is public
      </label>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={submitting || !form.title.trim() || !form.summary.trim()}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Saving..." : notice ? "Save changes" : "Create notice"}
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
