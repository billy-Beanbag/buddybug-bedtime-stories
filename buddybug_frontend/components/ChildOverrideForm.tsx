"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPatch } from "@/lib/api";
import type { ChildControlOverrideRead, ChildProfileRead } from "@/lib/types";

interface ChildOverrideFormProps {
  childProfile: ChildProfileRead;
  token: string;
  onUpdated?: () => Promise<void> | void;
}

function nullableBooleanLabel(value: boolean | null) {
  if (value === null) {
    return "Inherit";
  }
  return value ? "On" : "Off";
}

export function ChildOverrideForm({ childProfile, token, onUpdated }: ChildOverrideFormProps) {
  const [override, setOverride] = useState<ChildControlOverrideRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadOverride() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiGet<ChildControlOverrideRead>(`/parental-controls/children/${childProfile.id}`, { token });
        setOverride(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load child override");
      } finally {
        setLoading(false);
      }
    }

    void loadOverride();
  }, [childProfile.id, token]);

  async function updateOverride(patch: Partial<ChildControlOverrideRead>) {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const response = await apiPatch<ChildControlOverrideRead>(
        `/parental-controls/children/${childProfile.id}`,
        patch,
        { token },
      );
      setOverride(response);
      await onUpdated?.();
      setMessage("Child override updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update child override");
    } finally {
      setSaving(false);
    }
  }

  if (loading || !override) {
    return (
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <p className="text-sm text-slate-600">Loading controls for {childProfile.display_name}...</p>
      </section>
    );
  }

  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{childProfile.display_name}</h3>
        <p className="mt-1 text-sm text-slate-600">
          Optional child-specific overrides. Leave inherited where possible.
        </p>
      </div>

      <div className="grid gap-3">
        {[
          ["bedtime_mode_enabled", "Bedtime mode"],
          ["allow_audio_autoplay", "Audio autoplay"],
          ["allow_8_12_content", "8-12 content"],
          ["allow_premium_voice_content", "Premium voices"],
          ["quiet_mode_enabled", "Quiet mode"],
        ].map(([field, label]) => (
          <div key={field} className="rounded-2xl bg-slate-50 px-4 py-3">
            <div className="mb-2 text-sm font-medium text-slate-800">{label}</div>
            <div className="flex gap-2">
              {[null, true, false].map((value, index) => (
                <button
                  key={`${field}-${index}`}
                  type="button"
                  disabled={saving}
                  onClick={() => void updateOverride({ [field]: value } as Partial<ChildControlOverrideRead>)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                    override[field as keyof ChildControlOverrideRead] === value
                      ? "bg-slate-900 text-white"
                      : "border border-slate-200 bg-white text-slate-700"
                  }`}
                >
                  {nullableBooleanLabel(value)}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Maximum age band</span>
        <select
          value={override.max_allowed_age_band ?? ""}
          onChange={(event) =>
            void updateOverride({
              max_allowed_age_band: event.target.value || null,
            })
          }
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
        >
          <option value="">Inherit</option>
          <option value="3-7">3-7</option>
          <option value="8-12">8-12</option>
        </select>
      </label>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
    </section>
  );
}
