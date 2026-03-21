"use client";

import Link from "next/link";

import { useAuth } from "@/context/AuthContext";
import { getOnboardingRoute, useOnboarding } from "@/context/OnboardingContext";

const STEP_COPY: Record<string, string> = {
  welcome: "See what Buddybug does and how getting started works.",
  child_setup: "Create a child profile so stories and progress feel more personal.",
  preferences: "Choose age band and language defaults for the family account.",
  bedtime_mode: "Take a quick look at bedtime mode and parental controls.",
  first_story: "Open a first story so Buddybug can start feeling useful right away.",
};

export function ContinueOnboardingCard() {
  const { isAuthenticated } = useAuth();
  const { state, isLoading, shouldShowOnboarding } = useOnboarding();

  if (!isAuthenticated || isLoading || !shouldShowOnboarding || !state) {
    return null;
  }

  return (
    <section className="rounded-[2rem] border border-indigo-100 bg-indigo-50/90 p-6 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-700">Continue setup</p>
      <h2 className="mt-3 text-2xl font-semibold text-slate-900">Finish getting started with Buddybug</h2>
      <p className="mt-2 text-sm leading-6 text-slate-700">
        {STEP_COPY[state.current_step] || "Pick up where you left off and head toward your first family story session."}
      </p>
      <Link
        href={getOnboardingRoute(state.current_step)}
        className="mt-5 inline-flex rounded-2xl bg-indigo-600 px-4 py-3 font-medium text-white hover:bg-indigo-500"
      >
        Continue setup
      </Link>
    </section>
  );
}
