"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useOnboarding } from "@/context/OnboardingContext";
import { trackOnboardingStepCompleted } from "@/lib/analytics";
import { useLocale } from "@/context/LocaleContext";

export function BedtimeModeStep() {
  const router = useRouter();
  const { token, user } = useAuth();
  const { locale } = useLocale();
  const { selectedChildProfile } = useChildProfiles();
  const { advanceOnboarding } = useOnboarding();
  const [submitting, setSubmitting] = useState(false);

  async function handleContinue() {
    setSubmitting(true);
    try {
      const response = await advanceOnboarding({
        next_step: "first_story",
        bedtime_mode_reviewed: true,
      });
      void trackOnboardingStepCompleted("bedtime_mode", {
        token,
        user,
        language: locale,
        childProfileId: selectedChildProfile?.id,
        source: "bedtime_mode_continue",
      });
      router.push(response?.recommended_next_route || "/onboarding/first-story");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <OnboardingShell
      step="bedtime_mode"
      title="A quick bedtime mode intro"
      description="Buddybug includes simple family controls so calmer story sessions are easier to repeat."
    >
      <div className="space-y-4">
        <div className="grid gap-3">
          <div className="rounded-2xl border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-4 text-white shadow-[0_18px_45px_rgba(30,41,59,0.16)]">
            <h3 className="font-semibold text-white">Bedtime mode</h3>
            <p className="mt-2 text-sm text-indigo-100">
              Keeps reading sessions calmer with more bedtime-friendly behavior and less friction before sleep.
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-4 text-white shadow-[0_18px_45px_rgba(30,41,59,0.16)]">
            <h3 className="font-semibold text-white">Parental controls</h3>
            <p className="mt-2 text-sm text-indigo-100">
              Manage autoplay, age-band access, and other safety defaults without leaving the family account.
            </p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-[linear-gradient(135deg,#1e1b4b_0%,#312e81_55%,#4338ca_100%)] p-4 text-white shadow-[0_18px_45px_rgba(30,41,59,0.16)]">
            <h3 className="font-semibold text-white">Flexible later</h3>
            <p className="mt-2 text-sm text-indigo-100">
              You can keep going now and fine-tune these controls later from the settings area.
            </p>
          </div>
        </div>
        <Link
          href="/parental-controls"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900 shadow-sm"
        >
          Review parental controls
        </Link>
        <button
          type="button"
          onClick={handleContinue}
          disabled={submitting}
          className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Continuing..." : "Continue to first story"}
        </button>
      </div>
    </OnboardingShell>
  );
}
