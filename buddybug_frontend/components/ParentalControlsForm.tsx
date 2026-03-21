"use client";

import { useEffect, useState } from "react";

import type { ParentalControlSettingsRead } from "@/lib/types";

interface ParentalControlsFormProps {
  settings: ParentalControlSettingsRead;
  onSave: (payload: Partial<ParentalControlSettingsRead>) => Promise<unknown>;
}

export function ParentalControlsForm({ settings, onSave }: ParentalControlsFormProps) {
  const [form, setForm] = useState({
    bedtime_mode_default: settings.bedtime_mode_default,
    allow_audio_autoplay: settings.allow_audio_autoplay,
    allow_8_12_content: settings.allow_8_12_content,
    allow_premium_voice_content: settings.allow_premium_voice_content,
    hide_adventure_content_at_bedtime: settings.hide_adventure_content_at_bedtime,
    max_allowed_age_band: settings.max_allowed_age_band,
    quiet_mode_default: settings.quiet_mode_default,
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm({
      bedtime_mode_default: settings.bedtime_mode_default,
      allow_audio_autoplay: settings.allow_audio_autoplay,
      allow_8_12_content: settings.allow_8_12_content,
      allow_premium_voice_content: settings.allow_premium_voice_content,
      hide_adventure_content_at_bedtime: settings.hide_adventure_content_at_bedtime,
      max_allowed_age_band: settings.max_allowed_age_band,
      quiet_mode_default: settings.quiet_mode_default,
    });
  }, [settings]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await onSave(form);
      setMessage("Parental controls updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update parental controls");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Account defaults</h2>
        <p className="mt-1 text-sm text-slate-600">These defaults apply when a child does not have an override.</p>
      </div>

      <div className="grid gap-3 text-sm text-slate-700">
        {[
          ["bedtime_mode_default", "Enable bedtime mode by default"],
          ["allow_audio_autoplay", "Allow audio autoplay"],
          ["allow_8_12_content", "Allow 8-12 content"],
          ["allow_premium_voice_content", "Allow premium narration voices"],
          ["hide_adventure_content_at_bedtime", "Hide adventure content at bedtime"],
          ["quiet_mode_default", "Prefer quiet mode"],
        ].map(([key, label]) => (
          <label key={key} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
            <span>{label}</span>
            <input
              type="checkbox"
              checked={Boolean(form[key as keyof typeof form])}
              onChange={(event) => setForm((current) => ({ ...current, [key]: event.target.checked }))}
            />
          </label>
        ))}
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Maximum allowed age band</span>
        <select
          value={form.max_allowed_age_band}
          onChange={(event) => setForm((current) => ({ ...current, max_allowed_age_band: event.target.value }))}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
        >
          <option value="3-7">3-7</option>
          <option value="8-12">8-12</option>
        </select>
      </label>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <button
        type="submit"
        disabled={saving}
        className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {saving ? "Saving..." : "Save parental defaults"}
      </button>
    </form>
  );
}
