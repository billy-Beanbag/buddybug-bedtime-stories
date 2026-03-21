"use client";

import { useEffect, useState } from "react";

import type { PrivacyPreferenceRead } from "@/lib/types";

interface PrivacyPreferencesFormProps {
  preferences: PrivacyPreferenceRead | null;
  saving?: boolean;
  onSubmit: (value: {
    marketing_email_opt_in: boolean;
    product_updates_opt_in: boolean;
    analytics_personalization_opt_in: boolean;
    allow_recommendation_personalization: boolean;
  }) => Promise<void>;
}

export function PrivacyPreferencesForm({
  preferences,
  saving = false,
  onSubmit,
}: PrivacyPreferencesFormProps) {
  const [form, setForm] = useState({
    marketing_email_opt_in: false,
    product_updates_opt_in: true,
    analytics_personalization_opt_in: false,
    allow_recommendation_personalization: true,
  });

  useEffect(() => {
    if (!preferences) {
      return;
    }
    setForm({
      marketing_email_opt_in: preferences.marketing_email_opt_in,
      product_updates_opt_in: preferences.product_updates_opt_in,
      analytics_personalization_opt_in: preferences.analytics_personalization_opt_in,
      allow_recommendation_personalization: preferences.allow_recommendation_personalization,
    });
  }, [preferences]);

  return (
    <form
      className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(form);
      }}
    >
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Privacy preferences</h2>
        <p className="mt-1 text-sm text-slate-600">
          Choose how Buddybug can contact you and whether personalization features should adapt to your family.
        </p>
      </div>

      <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.marketing_email_opt_in}
          onChange={(event) =>
            setForm((current) => ({ ...current, marketing_email_opt_in: event.target.checked }))
          }
          disabled={saving}
        />
        <span>Send occasional marketing emails about new Buddybug features, offers, or launches.</span>
      </label>

      <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.product_updates_opt_in}
          onChange={(event) =>
            setForm((current) => ({ ...current, product_updates_opt_in: event.target.checked }))
          }
          disabled={saving}
        />
        <span>Send product and service updates related to your Buddybug account.</span>
      </label>

      <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.analytics_personalization_opt_in}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              analytics_personalization_opt_in: event.target.checked,
            }))
          }
          disabled={saving}
        />
        <span>Allow Buddybug to use analytics signals for future personalization improvements.</span>
      </label>

      <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.allow_recommendation_personalization}
          onChange={(event) =>
            setForm((current) => ({
              ...current,
              allow_recommendation_personalization: event.target.checked,
            }))
          }
          disabled={saving}
        />
        <span>Allow reading recommendations to personalize based on your family’s activity and feedback.</span>
      </label>

      <button
        type="submit"
        disabled={saving}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {saving ? "Saving preferences..." : "Save privacy preferences"}
      </button>
    </form>
  );
}
