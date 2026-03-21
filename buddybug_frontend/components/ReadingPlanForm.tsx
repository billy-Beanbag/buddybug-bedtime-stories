"use client";

import { useEffect, useMemo, useState } from "react";

import type { ChildProfileRead, ReadingPlanRead } from "@/lib/types";

export interface ReadingPlanFormValues {
  child_profile_id: number | null;
  title: string;
  description: string;
  status: string;
  plan_type: string;
  preferred_age_band: string;
  preferred_language: string;
  preferred_content_lane_key: string;
  prefer_narration: boolean;
  sessions_per_week: number;
  target_days_csv: string;
  bedtime_mode_preferred: boolean;
}

interface ReadingPlanFormProps {
  childProfiles: ChildProfileRead[];
  selectedChildProfileId?: number | null;
  initialPlan?: ReadingPlanRead | null;
  submitting?: boolean;
  submitLabel: string;
  onSubmit: (values: ReadingPlanFormValues) => Promise<void> | void;
}

function buildInitialValues(initialPlan?: ReadingPlanRead | null, selectedChildProfileId?: number | null): ReadingPlanFormValues {
  if (initialPlan) {
    return {
      child_profile_id: initialPlan.child_profile_id,
      title: initialPlan.title,
      description: initialPlan.description || "",
      status: initialPlan.status,
      plan_type: initialPlan.plan_type,
      preferred_age_band: initialPlan.preferred_age_band || "",
      preferred_language: initialPlan.preferred_language || "",
      preferred_content_lane_key: initialPlan.preferred_content_lane_key || "",
      prefer_narration: initialPlan.prefer_narration,
      sessions_per_week: initialPlan.sessions_per_week,
      target_days_csv: initialPlan.target_days_csv || "",
      bedtime_mode_preferred: initialPlan.bedtime_mode_preferred,
    };
  }
  return {
    child_profile_id: selectedChildProfileId ?? null,
    title: "",
    description: "",
    status: "active",
    plan_type: "bedtime",
    preferred_age_band: "",
    preferred_language: "",
    preferred_content_lane_key: "",
    prefer_narration: false,
    sessions_per_week: 3,
    target_days_csv: "",
    bedtime_mode_preferred: true,
  };
}

export function ReadingPlanForm({
  childProfiles,
  selectedChildProfileId = null,
  initialPlan = null,
  submitting = false,
  submitLabel,
  onSubmit,
}: ReadingPlanFormProps) {
  const [form, setForm] = useState<ReadingPlanFormValues>(() => buildInitialValues(initialPlan, selectedChildProfileId));
  const [error, setError] = useState<string | null>(null);
  const selectedChildProfile = useMemo(
    () => childProfiles.find((item) => item.id === form.child_profile_id) || null,
    [childProfiles, form.child_profile_id],
  );

  useEffect(() => {
    setForm(buildInitialValues(initialPlan, selectedChildProfileId));
    setError(null);
  }, [initialPlan, selectedChildProfileId]);

  useEffect(() => {
    if (!selectedChildProfile || initialPlan) {
      return;
    }
    setForm((current) => ({
      ...current,
      preferred_age_band: current.preferred_age_band || selectedChildProfile.age_band,
      preferred_language: current.preferred_language || selectedChildProfile.language,
      preferred_content_lane_key: current.preferred_content_lane_key || selectedChildProfile.content_lane_key || "",
    }));
  }, [initialPlan, selectedChildProfile]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!form.title.trim()) {
      setError("Plan title is required.");
      return;
    }
    setError(null);
    await onSubmit(form);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">{initialPlan ? "Edit reading plan" : "Create reading plan"}</h2>
        <p className="mt-1 text-sm text-slate-600">
          Keep routines gentle and flexible, with a little structure for calmer story time.
        </p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Title</span>
        <input
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          placeholder="Bedtime routine for Daisy"
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Description</span>
        <textarea
          value={form.description}
          onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
          className="min-h-24 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          placeholder="A calm, repeatable reading rhythm for this part of the week."
        />
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Plan type</span>
          <select
            value={form.plan_type}
            onChange={(event) => setForm((current) => ({ ...current, plan_type: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="bedtime">Bedtime</option>
            <option value="narrated">Narrated</option>
            <option value="language_practice">Language practice</option>
            <option value="family_reading">Family reading</option>
            <option value="custom">Custom</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Status</span>
          <select
            value={form.status}
            onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="archived">Archived</option>
          </select>
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Scope</span>
          <select
            value={form.child_profile_id ?? ""}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                child_profile_id: event.target.value ? Number(event.target.value) : null,
              }))
            }
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="">Whole family</option>
            {childProfiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Sessions per week</span>
          <input
            type="number"
            min={1}
            max={7}
            value={form.sessions_per_week}
            onChange={(event) =>
              setForm((current) => ({ ...current, sessions_per_week: Math.max(1, Math.min(7, Number(event.target.value) || 1)) }))
            }
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          />
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Age band</span>
          <select
            value={form.preferred_age_band}
            onChange={(event) => setForm((current) => ({ ...current, preferred_age_band: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="">Flexible</option>
            <option value="3-7">3-7</option>
            <option value="8-12">8-12</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Language</span>
          <select
            value={form.preferred_language}
            onChange={(event) => setForm((current) => ({ ...current, preferred_language: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          >
            <option value="">Flexible</option>
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Content lane</span>
          <input
            value={form.preferred_content_lane_key}
            onChange={(event) => setForm((current) => ({ ...current, preferred_content_lane_key: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
            placeholder="bedtime_3_7"
          />
        </label>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Target days</span>
        <input
          value={form.target_days_csv}
          onChange={(event) => setForm((current) => ({ ...current, target_days_csv: event.target.value }))}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
          placeholder="mon,wed,fri"
        />
      </label>

      <div className="grid gap-3 text-sm text-slate-700">
        <label className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
          <span>Prefer narration when possible</span>
          <input
            type="checkbox"
            checked={form.prefer_narration}
            onChange={(event) => setForm((current) => ({ ...current, prefer_narration: event.target.checked }))}
          />
        </label>
        <label className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
          <span>Prefer bedtime mode feel</span>
          <input
            type="checkbox"
            checked={form.bedtime_mode_preferred}
            onChange={(event) => setForm((current) => ({ ...current, bedtime_mode_preferred: event.target.checked }))}
          />
        </label>
      </div>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
