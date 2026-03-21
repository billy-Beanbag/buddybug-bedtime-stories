"use client";

import { useEffect, useMemo, useState } from "react";

import type { ChildComfortProfileRead, ChildProfileRead } from "@/lib/types";

import { ComfortPreferenceChips } from "./ComfortPreferenceChips";

const MOOD_OPTIONS = ["Calm", "Cozy", "Playful", "Magical", "Gentle", "Curious"];
const STORY_TYPE_OPTIONS = ["Bedtime", "Friendship", "Animal Friends", "Magic", "Nature", "Adventure"];
const AVOID_OPTIONS = ["spooky", "loud", "fast-paced", "sad", "conflict-heavy"];
const GENTLE_PREFERENCE_TOGGLES: Array<{
  field: "prefer_narration" | "prefer_shorter_stories" | "extra_calm_mode";
  label: string;
}> = [
  { field: "prefer_narration", label: "Narration usually helps" },
  { field: "prefer_shorter_stories", label: "Shorter stories are a better fit" },
  { field: "extra_calm_mode", label: "Lean extra calm, especially at bedtime" },
];

export interface ChildComfortFormValues {
  favorite_characters_csv: string;
  favorite_moods_csv: string;
  favorite_story_types_csv: string;
  avoid_tags_csv: string;
  preferred_language: string;
  prefer_narration: boolean;
  prefer_shorter_stories: boolean;
  extra_calm_mode: boolean;
  bedtime_notes: string;
}

interface ChildComfortProfileFormProps {
  childProfile: ChildProfileRead;
  profile: ChildComfortProfileRead;
  submitting?: boolean;
  onSave: (values: ChildComfortFormValues) => Promise<void>;
}

function parseCsv(value: string | null | undefined) {
  if (!value) {
    return [];
  }
  return value
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

export function ChildComfortProfileForm({
  childProfile,
  profile,
  submitting = false,
  onSave,
}: ChildComfortProfileFormProps) {
  const [form, setForm] = useState<ChildComfortFormValues>({
    favorite_characters_csv: profile.favorite_characters_csv || "",
    favorite_moods_csv: profile.favorite_moods_csv || "",
    favorite_story_types_csv: profile.favorite_story_types_csv || "",
    avoid_tags_csv: profile.avoid_tags_csv || "",
    preferred_language: profile.preferred_language || "",
    prefer_narration: profile.prefer_narration,
    prefer_shorter_stories: profile.prefer_shorter_stories,
    extra_calm_mode: profile.extra_calm_mode,
    bedtime_notes: profile.bedtime_notes || "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm({
      favorite_characters_csv: profile.favorite_characters_csv || "",
      favorite_moods_csv: profile.favorite_moods_csv || "",
      favorite_story_types_csv: profile.favorite_story_types_csv || "",
      avoid_tags_csv: profile.avoid_tags_csv || "",
      preferred_language: profile.preferred_language || "",
      prefer_narration: profile.prefer_narration,
      prefer_shorter_stories: profile.prefer_shorter_stories,
      extra_calm_mode: profile.extra_calm_mode,
      bedtime_notes: profile.bedtime_notes || "",
    });
    setMessage(null);
    setError(null);
  }, [profile]);

  const selectedMoods = useMemo(() => parseCsv(form.favorite_moods_csv), [form.favorite_moods_csv]);
  const selectedStoryTypes = useMemo(() => parseCsv(form.favorite_story_types_csv), [form.favorite_story_types_csv]);
  const selectedAvoidTags = useMemo(() => parseCsv(form.avoid_tags_csv), [form.avoid_tags_csv]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    try {
      await onSave(form);
      setMessage("Comfort preferences updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save comfort preferences");
    }
  }

  function updateChipField(field: "favorite_moods_csv" | "favorite_story_types_csv" | "avoid_tags_csv", values: string[]) {
    setForm((current) => ({ ...current, [field]: values.join(", ") }));
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Comfort & story preferences</h2>
        <p className="mt-1 text-sm text-slate-600">
          Use gentle preferences for {childProfile.display_name} to help Buddybug lean calmer, warmer, and more familiar.
        </p>
      </div>

      <section className="space-y-3">
        <div>
          <h3 className="text-sm font-medium text-slate-900">Loves</h3>
          <p className="mt-1 text-sm text-slate-600">These are soft signals Buddybug can use when it picks stories.</p>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Favorite characters</span>
          <input
            value={form.favorite_characters_csv}
            onChange={(event) => setForm((current) => ({ ...current, favorite_characters_csv: event.target.value }))}
            placeholder="Luna, Pip, Moonbug"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          />
        </label>

        <ComfortPreferenceChips
          label="Favorite moods"
          description="Pick the feelings that usually land best."
          options={MOOD_OPTIONS}
          selected={selectedMoods}
          disabled={submitting}
          onChange={(values) => updateChipField("favorite_moods_csv", values)}
        />

        <ComfortPreferenceChips
          label="Favorite story types"
          description="Choose a few familiar story shapes to lean on."
          options={STORY_TYPE_OPTIONS}
          selected={selectedStoryTypes}
          disabled={submitting}
          onChange={(values) => updateChipField("favorite_story_types_csv", values)}
        />
      </section>

      <section className="space-y-3">
        <div>
          <h3 className="text-sm font-medium text-slate-900">Gentle preferences</h3>
          <p className="mt-1 text-sm text-slate-600">These help with bedtime packs, reading plans, and recommendations.</p>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Preferred language</span>
          <select
            value={form.preferred_language}
            onChange={(event) => setForm((current) => ({ ...current, preferred_language: event.target.value }))}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">Use child profile default ({childProfile.language.toUpperCase()})</option>
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
          </select>
        </label>

        <div className="grid gap-3 text-sm text-slate-700">
          {GENTLE_PREFERENCE_TOGGLES.map(({ field, label }) => (
            <label key={field} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
              <span>{label}</span>
              <input
                type="checkbox"
                checked={form[field]}
                onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.checked }))}
              />
            </label>
          ))}
        </div>
      </section>

      <ComfortPreferenceChips
        label="Try to avoid"
        description="These are gentle content signals, not strict blocks."
        options={AVOID_OPTIONS}
        selected={selectedAvoidTags}
        disabled={submitting}
        onChange={(values) => updateChipField("avoid_tags_csv", values)}
      />

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Bedtime note</span>
        <textarea
          value={form.bedtime_notes}
          onChange={(event) => setForm((current) => ({ ...current, bedtime_notes: event.target.value }))}
          placeholder="Example: Loves quiet moon stories and settles faster with narration."
          rows={4}
          maxLength={280}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
        />
      </label>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Saving..." : "Save comfort preferences"}
      </button>
    </form>
  );
}
