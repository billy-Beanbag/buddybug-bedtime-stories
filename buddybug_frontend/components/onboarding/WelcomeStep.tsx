"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect } from "react";

import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { useAuth } from "@/context/AuthContext";
import { trackOnboardingStarted } from "@/lib/analytics";
import { useLocale } from "@/context/LocaleContext";

const STARTED_STORAGE_KEY = "buddybug.onboarding.started";

export function WelcomeStep() {
  const { token, user } = useAuth();
  const { locale } = useLocale();

  useEffect(() => {
    if (typeof window === "undefined" || window.sessionStorage.getItem(STARTED_STORAGE_KEY)) {
      return;
    }
    window.sessionStorage.setItem(STARTED_STORAGE_KEY, "1");
    void trackOnboardingStarted({
      token,
      user,
      language: locale,
      source: "welcome_step",
    });
  }, [locale, token, user]);

  return (
    <OnboardingShell
      step="welcome"
      title="Welcome to Buddybug"
      description="Buddybug is a story telling world that helps families with calmer bedtime stories, child-aware recommendations, and simple evening reading routines."
    >
      <div className="space-y-5">
        <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-5 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
          <div className="relative space-y-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-100">Start free with Buddybug</p>
              <h3 className="mt-3 text-2xl font-semibold text-white">See the full mood before you decide on anything else</h3>
              <p className="mt-3 text-sm leading-6 text-indigo-50">
                The Free Plan gives families a simple way to get started with Buddybug before deciding whether Premium fits
                their bedtime routine.
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
                  <p className="text-sm font-semibold text-white">Free plan includes</p>
                  <p className="mt-1 text-sm text-indigo-100">
                    3 stories per week, a smaller library, 1 child profile, and no bedtime packs or narration voice.
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
                  <p className="text-sm font-semibold text-white">Premium is $9.99</p>
                  <p className="mt-1 text-sm text-indigo-100">
                    Unlimited stories, full library access, bedtime packs, narration voices, unlimited child profiles, and personalised recommendations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">A growing illustrated library</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Explore hundreds of fully illustrated storybooks, with new stories arriving every day so Buddybug always feels
              fresh.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">Narration with choice</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Listen with numerous narration voices and tones, so story time can feel calm, playful, cozy, or dramatic.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">Made for different moments</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Choose gentle, calming stories for bedtime or lighter, more adventurous reads for daytime cuddles and quiet play.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">Multilingual and personal</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Set up child-aware profiles with language options, so recommendations, reading habits, and future picks feel more
              personal.
            </p>
          </div>
        </div>

        <div className="grid gap-3">
          <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-3 shadow-sm">
            <div className="relative mb-3 aspect-[16/10] overflow-hidden rounded-2xl">
              <Image src="/home/verity-card.png" alt="Verity character card" fill sizes="360px" className="object-cover" />
            </div>
            <p className="text-sm font-semibold text-slate-900">Verity</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Calm, caring, and reassuring, Verity brings a warm grown-up steadiness to BuddyBug's gentler story world.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-3 shadow-sm">
            <div className="relative mb-3 aspect-[16/10] overflow-hidden rounded-2xl">
              <Image src="/home/dolly-card.png" alt="Daphne character card" fill sizes="360px" className="object-cover" />
            </div>
            <p className="text-sm font-semibold text-slate-900">Daphne</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Curious, bright, and full of wonder, Daphne brings energy, imagination, and a sense of adventure to every story.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200/80 bg-white/80 p-3 shadow-sm">
            <div className="relative mb-3 aspect-[16/10] overflow-hidden rounded-2xl">
              <Image src="/home/daphne-card.png" alt="Dolly character card" fill sizes="360px" className="object-cover" />
            </div>
            <p className="text-sm font-semibold text-slate-900">Dolly</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">
              Sweet, playful, and cuddly, Dolly adds softness, comfort, and a cheerful little sparkle to BuddyBug adventures.
            </p>
          </div>
        </div>

        <Link
          href="/pricing"
          className="block w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900 shadow-sm"
        >
          Join now
        </Link>
      </div>
    </OnboardingShell>
  );
}
