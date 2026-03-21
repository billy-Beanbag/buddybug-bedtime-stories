"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import { useOnboarding } from "@/context/OnboardingContext";
import { trackOnboardingStepCompleted } from "@/lib/analytics";

export function PreferencesStep() {
  const router = useRouter();
  const { token, user } = useAuth();
  const { locale, setLocale } = useLocale();
  const { selectedChildProfile } = useChildProfiles();
  const { state, advanceOnboarding } = useOnboarding();
  const [ageBand, setAgeBand] = useState("3-7");
  const [language, setLanguage] = useState("en");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setAgeBand(state?.preferred_age_band || selectedChildProfile?.age_band || "3-7");
    setLanguage(state?.preferred_language || selectedChildProfile?.language || locale);
  }, [locale, selectedChildProfile?.age_band, selectedChildProfile?.language, state?.preferred_age_band, state?.preferred_language]);

  async function handleContinue() {
    setSubmitting(true);
    try {
      const response = await advanceOnboarding({
        next_step: "bedtime_mode",
        preferred_age_band: ageBand,
        preferred_language: language,
      });
      setLocale(language);
      void trackOnboardingStepCompleted("preferences", {
        token,
        user,
        language,
        childProfileId: selectedChildProfile?.id,
        source: "preferences_continue",
      });
      router.push(response?.recommended_next_route || "/onboarding/bedtime");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <OnboardingShell
      step="preferences"
      title="Choose age band and language"
      description="These defaults help Buddybug suggest the right story lane and keep reading surfaces comfortable from the start."
    >
      <div className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block rounded-2xl border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-4 text-white shadow-[0_18px_45px_rgba(30,41,59,0.16)]">
            <span className="mb-2 block text-sm font-medium text-indigo-100">Preferred age band</span>
            <select
              value={ageBand}
              onChange={(event) => setAgeBand(event.target.value)}
              className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none"
            >
              <option value="3-7">3-7</option>
              <option value="8-12">8-12</option>
            </select>
            <p className="mt-2 text-xs text-indigo-100">You can still adjust child profiles and family controls later.</p>
          </label>
          <label className="block rounded-2xl border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-4 text-white shadow-[0_18px_45px_rgba(30,41,59,0.16)]">
            <span className="mb-2 block text-sm font-medium text-indigo-100">Preferred reading language</span>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
            </select>
            <p className="mt-2 text-xs text-indigo-100">This helps with getting-started recommendations and app copy defaults.</p>
          </label>
        </div>
        <div className="rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-4 text-sm text-indigo-900">
          Buddybug uses these preferences as a starting point, not a lock. Families can keep multiple child profiles with different setups.
        </div>
        <button
          type="button"
          onClick={handleContinue}
          disabled={submitting}
          className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Saving preferences..." : "Continue to bedtime setup"}
        </button>
      </div>
    </OnboardingShell>
  );
}
