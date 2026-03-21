"use client";

import { useEffect, useState } from "react";

import type { NotificationPreferenceRead } from "@/lib/types";

export function NotificationPreferencesForm({
  preference,
  onSave,
}: {
  preference: NotificationPreferenceRead;
  onSave: (payload: Partial<NotificationPreferenceRead>) => Promise<void>;
}) {
  const [form, setForm] = useState({
    enable_in_app: preference.enable_in_app,
    enable_email_placeholder: preference.enable_email_placeholder,
    enable_bedtime_reminders: preference.enable_bedtime_reminders,
    enable_new_story_alerts: preference.enable_new_story_alerts,
    enable_weekly_digest: preference.enable_weekly_digest,
    quiet_hours_start: preference.quiet_hours_start || "",
    quiet_hours_end: preference.quiet_hours_end || "",
    timezone: preference.timezone || "",
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setForm({
      enable_in_app: preference.enable_in_app,
      enable_email_placeholder: preference.enable_email_placeholder,
      enable_bedtime_reminders: preference.enable_bedtime_reminders,
      enable_new_story_alerts: preference.enable_new_story_alerts,
      enable_weekly_digest: preference.enable_weekly_digest,
      quiet_hours_start: preference.quiet_hours_start || "",
      quiet_hours_end: preference.quiet_hours_end || "",
      timezone: preference.timezone || "",
    });
  }, [preference]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await onSave({
        ...form,
        quiet_hours_start: form.quiet_hours_start || null,
        quiet_hours_end: form.quiet_hours_end || null,
        timezone: form.timezone || null,
      });
      setMessage("Notification preferences updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update notification preferences");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Notification preferences</h2>
        <p className="mt-1 text-sm text-slate-600">Choose how Buddybug fits into your family routine.</p>
      </div>

      <div className="grid gap-3 text-sm text-slate-700">
        {[
          ["enable_in_app", "Enable in-app notifications"],
          ["enable_email_placeholder", "Enable email placeholders"],
          ["enable_bedtime_reminders", "Enable bedtime reminders"],
          ["enable_new_story_alerts", "Enable new story alerts"],
          ["enable_weekly_digest", "Enable weekly digest placeholder"],
        ].map(([field, label]) => (
          <label key={field} className="flex items-center justify-between rounded-2xl bg-slate-50 px-4 py-3">
            <span>{label}</span>
            <input
              type="checkbox"
              checked={Boolean(form[field as keyof typeof form])}
              onChange={(event) => setForm((current) => ({ ...current, [field]: event.target.checked }))}
            />
          </label>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Quiet hours start</span>
          <input
            value={form.quiet_hours_start}
            onChange={(event) => setForm((current) => ({ ...current, quiet_hours_start: event.target.value }))}
            placeholder="20:00"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Quiet hours end</span>
          <input
            value={form.quiet_hours_end}
            onChange={(event) => setForm((current) => ({ ...current, quiet_hours_end: event.target.value }))}
            placeholder="07:00"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          />
        </label>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Timezone</span>
        <input
          value={form.timezone}
          onChange={(event) => setForm((current) => ({ ...current, timezone: event.target.value }))}
          placeholder="Europe/London"
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
        />
      </label>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <button
        type="submit"
        disabled={saving}
        className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {saving ? "Saving..." : "Save notification preferences"}
      </button>
    </form>
  );
}
