"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppSectionCard } from "@/components/AppSectionCard";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type { PrivacyPreferenceRead } from "@/lib/types";

export default function SettingsPrivacyPage() {
  const { token, isAuthenticated } = useAuth();
  const [privacyPreference, setPrivacyPreference] = useState<PrivacyPreferenceRead | null>(null);

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setPrivacyPreference(null);
      return;
    }

    void apiGet<PrivacyPreferenceRead>("/privacy/me/preferences", { token })
      .then((response) => setPrivacyPreference(response))
      .catch(() => setPrivacyPreference(null));
  }, [isAuthenticated, token]);

  return (
    <div className="space-y-4">
      <AppSectionCard
        title="Privacy settings"
        description="Privacy and consent are grouped here to match how a future packaged app would present family-safe controls."
      >
        {privacyPreference ? (
          <dl className="grid gap-3 text-sm">
            <div className="rounded-2xl bg-slate-50 px-4 py-3">
              <dt className="text-slate-500">Marketing emails</dt>
              <dd className="mt-1 font-medium text-slate-900">
                {privacyPreference.marketing_email_opt_in ? "Enabled" : "Disabled"}
              </dd>
            </div>
            <div className="rounded-2xl bg-slate-50 px-4 py-3">
              <dt className="text-slate-500">Recommendation personalization</dt>
              <dd className="mt-1 font-medium text-slate-900">
                {privacyPreference.allow_recommendation_personalization ? "Enabled" : "Disabled"}
              </dd>
            </div>
          </dl>
        ) : (
          <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
            Open the privacy center to review preferences, legal acceptance, and data requests.
          </p>
        )}
      </AppSectionCard>

      <AppSectionCard title="Open privacy center">
        <Link
          href="/privacy"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
        >
          Open Privacy & Data
        </Link>
      </AppSectionCard>
    </div>
  );
}
