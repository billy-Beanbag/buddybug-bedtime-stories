"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { useOnboarding } from "@/context/OnboardingContext";
import { trackOnboardingSkipped } from "@/lib/analytics";
import { useLocale } from "@/context/LocaleContext";
import { OnboardingProgress } from "@/components/onboarding/OnboardingProgress";

interface OnboardingShellProps {
  step: string;
  title: string;
  description: string;
  children: ReactNode;
}

export function OnboardingShell({ step, title, description, children }: OnboardingShellProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, token, user } = useAuth();
  const { state, isLoading, skipOnboarding } = useOnboarding();
  const { locale } = useLocale();

  async function handleSkip() {
    try {
      await skipOnboarding();
      void trackOnboardingSkipped({
        token,
        user,
        language: locale,
        source: step,
      });
    } finally {
      router.push("/library");
    }
  }

  if (authLoading || isLoading) {
    return <LoadingState message="Preparing setup..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to continue setup"
          description="Onboarding is available for authenticated family accounts."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white"
          >
            Create account
          </Link>
        </div>
      </div>
    );
  }

  if (!state) {
    return <EmptyState title="Setup unavailable" description="We couldn't load your onboarding progress right now." />;
  }

  return (
    <section className="space-y-4">
      <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_40%,#302a6f_72%,#47377a_100%)] p-6 text-white shadow-[0_24px_70px_rgba(30,41,59,0.22)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.22),transparent_26%),radial-gradient(circle_at_20%_20%,rgba(129,140,248,0.24),transparent_32%)]" />
        <div className="pointer-events-none absolute -right-10 top-8 h-36 w-36 rounded-full bg-amber-100/10 blur-3xl" />
        <div className="relative space-y-5">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Link
                href="/pricing"
                className="rounded-full border border-emerald-300/20 bg-emerald-300/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100"
              >
                Free plan available
              </Link>
            </div>
            <h2 className="mt-4 text-3xl font-semibold text-white">{title}</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-indigo-50">{description}</p>
            <div className="mt-6">
              {step === "welcome" ? (
                <button
                  type="button"
                  className="inline-flex min-w-[16rem] items-center justify-center rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white"
                >
                  Download a free BuddyBug story
                </button>
              ) : (
                <OnboardingProgress currentStep={state.current_step || step} />
              )}
            </div>
          </div>

          <div className="space-y-3">
            <div className="overflow-hidden rounded-[1.75rem] border border-white/15 bg-white/10 p-3 shadow-[0_18px_45px_rgba(15,23,42,0.16)]">
              <div className="relative aspect-[4/5] rounded-[1.25rem] bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.14),_rgba(15,23,42,0.08)_58%,_rgba(15,23,42,0.02))]">
                <Image
                  src="/home/verity-reading.jpeg"
                  alt="Verity reading with Daphne and Dolly"
                  fill
                  sizes="(max-width: 1024px) 100vw, 360px"
                  className="object-cover object-center"
                  priority
                />
              </div>
            </div>

            <div className="rounded-[1.5rem] border border-white/10 bg-white/10 px-4 py-4 text-center">
              <p className="text-sm font-semibold text-white">Verity, Daphne, Dolly & BuddyBug</p>
              <p className="mt-1 text-sm leading-6 text-indigo-100">
                Join this happy little family on adventures, mysteries and lots of fun, with new bedtime stories every
                night.
              </p>
            </div>

            <div className="rounded-[1.5rem] border border-white/10 bg-white/10 px-4 py-4 text-center">
              <p className="text-sm font-semibold text-white">Start free tonight</p>
              <Link
                href="/pricing"
                className="mt-4 inline-flex min-w-[10rem] items-center justify-center rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white"
              >
                JOIN NOW
              </Link>
            </div>
          </div>
        </div>
      </div>
      <div className="rounded-[2rem] border border-white/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(238,242,255,0.9))] p-6 shadow-sm backdrop-blur">
        {children}
      </div>
    </section>
  );
}
