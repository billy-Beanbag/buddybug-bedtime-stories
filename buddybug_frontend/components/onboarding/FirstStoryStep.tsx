"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { LoadingState } from "@/components/LoadingState";
import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import { apiGet, resolveApiUrl } from "@/lib/api";
import type { DailyStorySuggestionResponse } from "@/lib/types";

export function FirstStoryStep() {
  const router = useRouter();
  const { token, isAuthenticated } = useAuth();
  const { locale } = useLocale();
  const { selectedChildProfile } = useChildProfiles();
  const [suggestion, setSuggestion] = useState<DailyStorySuggestionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setSuggestion(null);
      setLoading(false);
      return;
    }

    async function loadSuggestion() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiGet<DailyStorySuggestionResponse>("/notifications/me/daily-story", {
          token,
          query: { child_profile_id: selectedChildProfile?.id },
        });
        setSuggestion(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load your first story suggestion");
      } finally {
        setLoading(false);
      }
    }

    void loadSuggestion();
  }, [isAuthenticated, selectedChildProfile?.id, token]);

  function handleOpenStory() {
    if (!suggestion?.book) {
      return;
    }
    router.push(`/reader/${suggestion.book.book_id}`);
  }

  return (
    <OnboardingShell
      step="first_story"
      title="Start your first story"
      description="The fastest way to make Buddybug click is to open a story now. We’ll mark setup complete once your first read session starts."
    >
      {loading ? (
        <LoadingState message="Picking a first story..." />
      ) : (
        <div className="space-y-5">
          {suggestion?.book ? (
            <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-4 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
              <div className="relative grid gap-4 sm:grid-cols-[auto_1fr]">
                <div className="h-44 w-32 overflow-hidden rounded-[1.5rem] border border-white/10 bg-slate-900/40">
                  {suggestion.book.cover_image_url ? (
                    <img
                      src={resolveApiUrl(suggestion.book.cover_image_url)}
                      alt={suggestion.book.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center px-4 text-center text-sm text-indigo-100">
                      Cover preview coming next
                    </div>
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium uppercase tracking-[0.16em] text-indigo-100">
                    {selectedChildProfile ? `${selectedChildProfile.display_name}'s first pick` : "Today's suggested story"}
                  </p>
                  <h3 className="mt-3 text-2xl font-semibold text-white">{suggestion.book.title}</h3>
                  <p className="mt-2 text-sm text-indigo-100">
                    Age band {suggestion.book.age_band} in {suggestion.book.language.toUpperCase()}.
                  </p>
                  <p className="mt-4 text-sm leading-6 text-indigo-50">
                    Open this story to start a real reading session. Buddybug will remember where you left off and keep future picks more relevant.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2 text-xs font-medium text-indigo-50">
                    <span className="rounded-full border border-white/10 bg-white/10 px-3 py-2">Free plan friendly</span>
                    <span className="rounded-full border border-white/10 bg-white/10 px-3 py-2">A first feel for Buddybug</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-900">
              {error || "We could not pick a daily suggestion right now, but you can still head straight into the library."}
            </div>
          )}
          {suggestion?.book ? (
            <button
              type="button"
              onClick={handleOpenStory}
              className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white"
            >
              Read our first story
            </button>
          ) : null}
          <div className="grid gap-3 sm:grid-cols-2">
            <Link
              href="/library"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900 shadow-sm"
            >
              Browse library
            </Link>
            <Link
              href="/bedtime-pack"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900 shadow-sm"
            >
              Open bedtime pack
            </Link>
          </div>
          <div className="rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-4 text-sm text-indigo-900">
            You can stay on the free plan while getting a real feel for Verity, Daphne, Dolly, and the wider Buddybug story world.
          </div>
        </div>
      )}
    </OnboardingShell>
  );
}
