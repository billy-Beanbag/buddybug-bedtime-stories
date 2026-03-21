"use client";

import Link from "next/link";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";

export function GettingStartedPageContent() {
  const { isAuthenticated, isLoading, hasPremiumAccess } = useAuth();
  const { childProfiles, isLoading: childProfilesLoading } = useChildProfiles();

  if (isLoading || childProfilesLoading) {
    return <LoadingState message="Preparing your Buddybug setup..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Create an account to get started"
          description="Getting started is available once your Buddybug account has been created."
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

  const hasChildProfiles = childProfiles.length > 0;

  return (
    <section className="space-y-5">
      <div className="rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-100">Getting started</p>
        <h1 className="mt-3 text-3xl font-semibold">Welcome to Buddybug</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-indigo-50">
          Buddybug is built to help families find the right story for the right moment, from calming bedtime reads to funny,
          adventurous daytime stories.
        </p>
        <div className="mt-5 rounded-2xl border border-white/10 bg-white/10 px-4 py-4 text-sm text-indigo-50">
          New stories arrive regularly, recommendations become more personal over time, and your child's reading world stays
          attached to one Buddybug account from the very beginning.
        </div>
        {hasPremiumAccess ? (
          <div className="mt-4 rounded-2xl border border-emerald-300/20 bg-emerald-300/15 px-4 py-4 text-sm text-emerald-50">
            Premium is active on your account, so full library access, bedtime packs, narration voices, and expanded family
            setup are ready as you continue.
          </div>
        ) : null}
      </div>

      <div className="grid gap-4">
        <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">What Buddybug can do</h2>
          <div className="mt-4 grid gap-3">
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50 px-4 py-4">
              <p className="font-semibold text-slate-900">Fresh story moments</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Buddybug keeps your family reading with new stories every day and a library that can grow with your routine.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50 px-4 py-4">
              <p className="font-semibold text-slate-900">Child-aware personalisation</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Reading habits, age band, language, and future recommendations can stay tailored to the child profile you set up.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50 px-4 py-4">
              <p className="font-semibold text-slate-900">Different moods for different times</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Use Buddybug for calmer bedtime stories, or switch into lighter, funny, adventurous reading during the day.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">What comes next</h2>
          <div className="mt-4 grid gap-3">
            <div className="rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-4 text-sm leading-6 text-indigo-950">
              Buddybug is starting with younger-family reading, and we plan to introduce dedicated sections for ages 8-11 and
              12+ later on.
            </div>
            <div className="rounded-2xl border border-slate-200/80 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-600">
              The next step is to {hasChildProfiles ? "confirm or update" : "create"} a child profile so Buddybug can start
              with the right reading lane and recommendations.
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Link
          href="/getting-started/child"
          className="rounded-2xl bg-indigo-600 px-4 py-3 text-center font-medium text-white hover:bg-indigo-500"
        >
          {hasChildProfiles ? "Continue with child setup" : "Set up child profile"}
        </Link>
        <Link
          href="/library"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          Go to library
        </Link>
      </div>
    </section>
  );
}
