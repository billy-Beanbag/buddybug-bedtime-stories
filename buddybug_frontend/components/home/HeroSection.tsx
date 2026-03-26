"use client";

import Image from "next/image";
import Link from "next/link";
import { useMemo } from "react";

import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";

function PrimaryButton({ href, children }: { href: string; children: string }) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/15"
    >
      {children}
    </Link>
  );
}

function SecondaryButton({ href, children }: { href: string; children: string }) {
  return (
    <Link
      href={href}
      className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/15"
    >
      {children}
    </Link>
  );
}

export function HeroSection() {
  const { isAuthenticated, isLoading } = useAuth();
  const { childProfiles, selectedChildProfile, isLoading: childProfilesLoading } = useChildProfiles();

  const startReadingHref = isAuthenticated ? "/library" : "/register";
  const bedtimePackHref = isAuthenticated ? "/bedtime-pack" : "/register";
  const primaryLabel = isLoading ? "Start Reading" : isAuthenticated ? "Open Library" : "Start Reading";
  const heroChildProfile = selectedChildProfile || childProfiles[0] || null;
  const currentYear = new Date().getFullYear();
  const childAgeLabel = useMemo(() => {
    if (!heroChildProfile?.birth_year) {
      return heroChildProfile ? `ages ${heroChildProfile.age_band}` : null;
    }
    const computedAge = currentYear - heroChildProfile.birth_year;
    return computedAge > 0 && computedAge < 18 ? `age ${computedAge}` : `ages ${heroChildProfile.age_band}`;
  }, [currentYear, heroChildProfile]);
  const childProfileHeading = childProfilesLoading
    ? "Loading child profile"
    : heroChildProfile
      ? `${heroChildProfile.display_name}${childAgeLabel ? `, ${childAgeLabel}` : ""}`
      : isAuthenticated
        ? "Add your child's profile"
        : "Personalised child profile";
  const childProfileDescription = childProfilesLoading
    ? "Bringing in the bedtime profile for this account."
    : heroChildProfile
      ? `Reading in ${heroChildProfile.language.toUpperCase()} with story suggestions shaped for ${heroChildProfile.display_name}.`
      : isAuthenticated
        ? "Add a child profile so Buddybug can tailor language, age range, and story suggestions to your family."
        : "Sign in to see your child's live Buddybug profile, language, and age-based story setup here.";

  return (
    <section className="relative overflow-hidden rounded-[2.5rem] bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_40%,#302a6f_72%,#47377a_100%)] px-6 py-8 text-white shadow-[0_24px_70px_rgba(30,41,59,0.28)] sm:px-8 md:px-10 md:py-10">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.28),transparent_26%),radial-gradient(circle_at_20%_20%,rgba(129,140,248,0.28),transparent_32%)]" />
      <div className="pointer-events-none absolute -right-10 top-8 h-36 w-36 rounded-full bg-amber-100/10 blur-3xl" />
      <div className="pointer-events-none absolute left-4 top-12 h-2 w-2 rounded-full bg-white/80 shadow-[70px_10px_0_rgba(255,255,255,0.7),130px_50px_0_rgba(255,255,255,0.55),220px_20px_0_rgba(255,255,255,0.55)]" />

      <div className="relative grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Calm bedtime stories for growing imaginations
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-indigo-50 sm:text-lg">
            Buddybug brings illustrated stories, narrated reading, child profiles, and gentle bedtime routines together
            in one warm family experience.
          </p>

          <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <PrimaryButton href={startReadingHref}>{primaryLabel}</PrimaryButton>
            <SecondaryButton href={bedtimePackHref}>Tonight's Bedtime Pack</SecondaryButton>
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-[2rem] border border-white/15 bg-white/10 p-5 backdrop-blur">
            <p className="text-xs uppercase tracking-[0.24em] text-indigo-100">Tonight's flow</p>
            <div className="mt-4 space-y-3">
              <div className="mx-auto max-w-sm overflow-hidden rounded-[1.75rem] border border-white/10 bg-white/10 shadow-[0_18px_45px_rgba(15,23,42,0.16)]">
                <div className="relative aspect-[4/5]">
                  <Image
                    src="/home/verity-reading.jpeg"
                    alt="Verity reading with Dolly and Daphne"
                    fill
                    sizes="(max-width: 1024px) 100vw, 420px"
                    className="object-cover object-center"
                    priority
                  />
                  <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-slate-950/30 to-transparent" />
                  <div className="absolute left-4 top-4 rounded-full bg-slate-950/55 px-3 py-1 text-xs font-semibold text-white backdrop-blur">
                    Storylight pick
                  </div>
                </div>
              </div>
              <div className="rounded-2xl bg-white/95 p-4 text-slate-900 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-600">Child Profile</p>
                <p className="mt-2 text-lg font-semibold">{childProfileHeading}</p>
                <p className="mt-1 text-sm text-slate-600">{childProfileDescription}</p>
              </div>
              <div className="rounded-2xl bg-white/12 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-indigo-100">Bedtime Pack</p>
                    <p className="mt-2 text-lg font-semibold">Moonlit Wind-Down</p>
                  </div>
                  <span className="rounded-full bg-amber-200 px-3 py-1 text-xs font-semibold text-slate-900">3 stories</span>
                </div>
                <div className="mt-4 grid gap-2">
                  {[
                    "Dolly and Daphne Find the Softest Star",
                    "Buddybug at the Window Light",
                    "Verity's Goodnight Lantern",
                  ].map((item, index) => (
                    <div
                      key={item}
                      className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/10 px-3 py-3 text-sm text-white"
                    >
                      <span>
                        {index + 1}. {item}
                      </span>
                      <span className="text-indigo-100">{index === 2 ? "Calmest finish" : "Ready"}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
