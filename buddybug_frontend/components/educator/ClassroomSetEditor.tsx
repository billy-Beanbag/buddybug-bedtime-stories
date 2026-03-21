"use client";

import { useEffect, useState } from "react";

import type { ClassroomSetRead } from "@/lib/types";

export interface ClassroomSetFormValue {
  title: string;
  description: string;
  age_band: string;
  language: string;
  is_active: boolean;
}

function toFormValue(classroomSet?: ClassroomSetRead | null): ClassroomSetFormValue {
  return {
    title: classroomSet?.title || "",
    description: classroomSet?.description || "",
    age_band: classroomSet?.age_band || "",
    language: classroomSet?.language || "en",
    is_active: classroomSet?.is_active ?? true,
  };
}

export function ClassroomSetEditor({
  classroomSet,
  submitting,
  submitLabel,
  onSubmit,
}: {
  classroomSet?: ClassroomSetRead | null;
  submitting: boolean;
  submitLabel: string;
  onSubmit: (value: ClassroomSetFormValue) => Promise<void>;
}) {
  const [form, setForm] = useState<ClassroomSetFormValue>(toFormValue(classroomSet));

  useEffect(() => {
    setForm(toFormValue(classroomSet));
  }, [classroomSet]);

  return (
    <form
      className="space-y-4 rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(form);
      }}
    >
      <div>
        <h2 className="text-xl font-semibold text-slate-900">
          {classroomSet ? "Edit classroom set" : "Create classroom set"}
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Keep educator collections focused, age-appropriate, and easy to reuse in shared reading time.
        </p>
      </div>
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Title</span>
        <input
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          placeholder="Week one read-alouds"
          required
        />
      </label>
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Description</span>
        <textarea
          value={form.description}
          onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
          className="min-h-24 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          placeholder="A practical reading set for classroom calm-down or literacy time."
        />
      </label>
      <div className="grid gap-4 sm:grid-cols-3">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Age band</span>
          <select
            value={form.age_band}
            onChange={(event) => setForm((current) => ({ ...current, age_band: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="">Any</option>
            <option value="3-7">3-7</option>
            <option value="8-12">8-12</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Language</span>
          <select
            value={form.language}
            onChange={(event) => setForm((current) => ({ ...current, language: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
          </select>
        </label>
        <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
          />
          Set is active
        </label>
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
