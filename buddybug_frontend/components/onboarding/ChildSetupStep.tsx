"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useOnboarding } from "@/context/OnboardingContext";
import { trackOnboardingStepCompleted } from "@/lib/analytics";
import { apiPost } from "@/lib/api";
import { useLocale } from "@/context/LocaleContext";
import type { ChildProfileSelectionResponse } from "@/lib/types";

export function ChildSetupStep() {
  const router = useRouter();
  const { token, user } = useAuth();
  const { locale } = useLocale();
  const { childProfiles, refreshChildProfiles, setSelectedChildProfile, selectedChildProfile } = useChildProfiles();
  const { advanceOnboarding } = useOnboarding();
  const [displayName, setDisplayName] = useState("");
  const [ageBand, setAgeBand] = useState<"3-7" | "8-12">("3-7");
  const [language, setLanguage] = useState("en");
  const [birthYear, setBirthYear] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const existingProfile = useMemo(() => selectedChildProfile || childProfiles[0] || null, [childProfiles, selectedChildProfile]);

  async function handleUseExistingProfile() {
    if (!existingProfile) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const response = await advanceOnboarding({
        next_step: "preferences",
        child_profile_created: true,
        preferred_age_band: existingProfile.age_band,
        preferred_language: existingProfile.language,
      });
      void trackOnboardingStepCompleted("child_setup", {
        token,
        user,
        language: locale,
        childProfileId: existingProfile.id,
        source: "existing_child_profile",
      });
      router.push(response?.recommended_next_route || "/onboarding/preferences");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }
    if (!displayName.trim()) {
      setError("Child display name is required.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const response = await apiPost<ChildProfileSelectionResponse>(
        "/child-profiles",
        {
          display_name: displayName.trim(),
          age_band: ageBand,
          language,
          birth_year: birthYear ? Number(birthYear) : null,
        },
        { token },
      );
      await refreshChildProfiles();
      setSelectedChildProfile(response.child_profile.id);
      const onboardingResponse = await advanceOnboarding({
        next_step: "preferences",
        child_profile_created: true,
        preferred_age_band: response.child_profile.age_band,
        preferred_language: response.child_profile.language,
      });
      void trackOnboardingStepCompleted("child_setup", {
        token,
        user,
        language: locale,
        childProfileId: response.child_profile.id,
        source: "child_profile_created",
      });
      router.push(onboardingResponse?.recommended_next_route || "/onboarding/preferences");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create child profile");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSkipChildSetup() {
    setSubmitting(true);
    setError(null);
    try {
      const response = await advanceOnboarding({ next_step: "preferences" });
      void trackOnboardingStepCompleted("child_setup", {
        token,
        user,
        language: locale,
        source: "child_setup_skipped",
      });
      router.push(response?.recommended_next_route || "/onboarding/preferences");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <OnboardingShell
      step="child_setup"
      title="Set up a child profile"
      description="This helps Buddybug keep age bands, languages, and bedtime suggestions child-aware from the first session."
    >
      <div className="space-y-5">
        {existingProfile ? (
          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[linear-gradient(135deg,#14532d_0%,#166534_45%,#15803d_100%)] p-4 text-white shadow-[0_18px_45px_rgba(21,128,61,0.18)]">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%)]" />
            <div className="relative">
            <h3 className="font-semibold text-white">You already have a child profile</h3>
            <p className="mt-2 text-sm text-emerald-50">
              {existingProfile.display_name} is ready with {existingProfile.age_band} stories in {existingProfile.language}.
            </p>
            <button
              type="button"
              onClick={handleUseExistingProfile}
              disabled={submitting}
              className="mt-4 w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 font-medium text-white disabled:opacity-60"
            >
              {submitting ? "Continuing..." : "Use this profile"}
            </button>
            </div>
          </div>
        ) : null}

        <form
          onSubmit={handleSubmit}
          className="relative space-y-4 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-5 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]"
        >
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
          <div className="relative">
          <div>
            <h3 className="font-semibold text-white">Create a profile now</h3>
            <p className="mt-1 text-sm text-indigo-100">Optional, but recommended so your first story feels more personal.</p>
          </div>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-indigo-100">Child display name</span>
            <input
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none placeholder:text-indigo-200/70"
              placeholder="Mia"
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-indigo-100">Age band</span>
              <select
                value={ageBand}
                onChange={(event) => setAgeBand(event.target.value as "3-7" | "8-12")}
                className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none"
              >
                <option value="3-7">3-7</option>
                <option value="8-12">8-12</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-indigo-100">Language</span>
              <select
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
                className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
            </label>
          </div>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-indigo-100">Birth year</span>
            <input
              value={birthYear}
              onChange={(event) => setBirthYear(event.target.value)}
              inputMode="numeric"
              className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none placeholder:text-indigo-200/70"
              placeholder="2019"
            />
          </label>
          {error ? <p className="text-sm text-rose-300">{error}</p> : null}
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 font-medium text-white backdrop-blur disabled:opacity-60"
          >
            {submitting ? "Saving profile..." : "Create child profile"}
          </button>
          </div>
        </form>

        <button
          type="button"
          onClick={handleSkipChildSetup}
          disabled={submitting}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-medium text-slate-900 shadow-sm disabled:opacity-60"
        >
          Continue without a child profile
        </button>
      </div>
    </OnboardingShell>
  );
}
