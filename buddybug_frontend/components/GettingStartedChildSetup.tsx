"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiPost } from "@/lib/api";
import type { ChildProfileSelectionResponse } from "@/lib/types";
import { useOnboarding } from "@/context/OnboardingContext";

export function GettingStartedChildSetup() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading: authLoading } = useAuth();
  const { childProfiles, refreshChildProfiles, setSelectedChildProfile, selectedChildProfile, isLoading } = useChildProfiles();
  const { completeOnboarding } = useOnboarding();
  const [displayName, setDisplayName] = useState("");
  const [ageBand, setAgeBand] = useState<"3-7" | "8-12">("3-7");
  const [language, setLanguage] = useState("en");
  const [birthYear, setBirthYear] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const existingProfile = useMemo(() => selectedChildProfile || childProfiles[0] || null, [childProfiles, selectedChildProfile]);

  async function finishSetup(nextChildProfileId?: number | null) {
    if (typeof nextChildProfileId === "number") {
      setSelectedChildProfile(nextChildProfileId);
    }
    await completeOnboarding();
    router.push("/library");
  }

  async function handleUseExistingProfile() {
    if (!existingProfile) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await finishSetup(existingProfile.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to continue");
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
      await finishSetup(response.child_profile.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create child profile");
      setSubmitting(false);
    }
  }

  if (authLoading || isLoading) {
    return <LoadingState message="Preparing child setup..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Create an account to continue"
          description="Child setup is available once you are signed in to Buddybug."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Log in
          </Link>
          <Link
            href="/register/free"
            className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white"
          >
            Create account
          </Link>
        </div>
      </div>
    );
  }

  return (
    <section className="space-y-5">
      <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-100">Child profile</p>
        <h1 className="mt-3 text-3xl font-semibold">Set up who Buddybug is reading for</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-indigo-50">
          This helps Buddybug keep age bands, languages, and future recommendations personal from the very first reading
          session.
        </p>
      </div>

      {existingProfile ? (
        <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#14532d_0%,#166534_45%,#15803d_100%)] p-5 text-white shadow-[0_18px_45px_rgba(21,128,61,0.18)]">
          <h2 className="text-xl font-semibold">You already have a child profile</h2>
          <p className="mt-2 text-sm text-emerald-50">
            {existingProfile.display_name} is ready with {existingProfile.age_band} stories in {existingProfile.language}.
          </p>
          <button
            type="button"
            onClick={handleUseExistingProfile}
            disabled={submitting}
            className="mt-4 w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 font-medium text-white disabled:opacity-60"
          >
            {submitting ? "Opening Buddybug..." : "Use this profile and enter Buddybug"}
          </button>
        </div>
      ) : null}

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm"
      >
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Create a child profile</h2>
          <p className="mt-2 text-sm text-slate-600">
            Start with one child profile now. You can add more later if your plan allows it.
          </p>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Child display name</span>
          <input
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400"
            placeholder="Mia"
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Age band</span>
            <select
              value={ageBand}
              onChange={(event) => setAgeBand(event.target.value as "3-7" | "8-12")}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400"
            >
              <option value="3-7">3-7</option>
              <option value="8-12">8-12</option>
            </select>
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Language</span>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
            </select>
          </label>
        </div>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Birth year</span>
          <input
            value={birthYear}
            onChange={(event) => setBirthYear(event.target.value)}
            inputMode="numeric"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-indigo-400"
            placeholder="2019"
          />
        </label>

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Saving profile..." : "Create child profile and enter Buddybug"}
        </button>

        <Link href="/getting-started" className="block text-center text-sm font-medium text-indigo-700">
          Back to getting started
        </Link>
      </form>
    </section>
  );
}
