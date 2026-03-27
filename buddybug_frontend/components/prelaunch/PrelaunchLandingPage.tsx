import Image from "next/image";
import Link from "next/link";

import { SignupForm } from "@/components/prelaunch/SignupForm";

export function PrelaunchLandingPage() {
  return (
    <div className="overflow-hidden">
      <section className="relative rounded-[2rem] border border-white/60 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(224,231,255,0.76))] px-5 py-8 shadow-[0_24px_70px_rgba(79,70,229,0.14)] sm:px-8 sm:py-10">
        <div className="absolute -left-14 top-8 h-36 w-36 rounded-full bg-indigo-200/45 blur-3xl" />
        <div className="absolute -right-10 bottom-10 h-44 w-44 rounded-full bg-fuchsia-200/30 blur-3xl" />
        <div className="relative grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div className="space-y-6">
            <div className="inline-flex rounded-full border border-indigo-200 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600">
              Gentle stories before launch
            </div>
            <div className="space-y-4">
              <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                Weekly bedtime stories for calmer evenings, delivered quietly to your inbox.
              </h1>
              <p className="max-w-xl text-base leading-7 text-slate-700 sm:text-lg">
                Buddybug is getting ready to launch. Join now and we&apos;ll send one free bedtime story each week, plus a
                personalised launch-day gift story made around your child&apos;s name and age.
              </p>
            </div>
            <div className="grid gap-3 text-sm text-slate-700 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4">
                <p className="font-semibold text-slate-950">One free story every week</p>
                <p className="mt-2 leading-6">Fresh, calm bedtime reading while Buddybug prepares for launch.</p>
              </div>
              <div className="rounded-2xl border border-white/70 bg-white/80 p-4">
                <p className="font-semibold text-slate-950">Private story links only</p>
                <p className="mt-2 leading-6">No gimmicks, no advertising, just your secure story email.</p>
              </div>
              <div className="overflow-hidden rounded-2xl border border-white/70 bg-[linear-gradient(180deg,#e0e7ff_0%,#eef2ff_100%)]">
                <div className="relative aspect-[4/5] w-full">
                  <Image
                    src="/home/verity-reading.jpeg"
                    alt="Verity reading with Dolly and Daphne"
                    fill
                    sizes="(max-width: 640px) 100vw, 240px"
                    className="object-cover object-center"
                    priority
                  />
                </div>
              </div>
            </div>
          </div>

          <SignupForm formId="hero-signup" title="Start receiving bedtime stories" attribution="hero" />
        </div>
      </section>

      <section className="mt-8 grid gap-5 lg:grid-cols-3">
        <article className="rounded-[2rem] border border-indigo-100 bg-white/88 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-500">How it works</p>
          <h2 className="mt-3 text-2xl font-semibold text-slate-950">Free weekly bedtime stories until launch</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Sign up with your email, your child&apos;s first name, and age. We&apos;ll send a secure story link right away, then
            we&apos;ll send a new age-appropriate fully illustrated story to you each week thereafter
          </p>
        </article>
        <article className="rounded-[2rem] border border-indigo-100 bg-white/88 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-500">Launch-day promise</p>
          <h2 className="mt-3 text-2xl font-semibold text-slate-950">A personalised gift story on launch day</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Every pre-launch family will receive a special Buddybug launch story shaped around the child&apos;s name and age
            provided to us at signup.
          </p>
        </article>
        <article className="rounded-[2rem] border border-indigo-100 bg-white/88 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-500">Parent reassurance</p>
          <h2 className="mt-3 text-2xl font-semibold text-slate-950">Simple, private, and light-touch</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            We only store the minimum amount of information needed to send stories. There&apos;s no public profile, no
            dashboard, no adverts or banners, and no hidden app area behind the scenes for subscribers.
          </p>
        </article>
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <div className="rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(79,70,229,0.98),rgba(99,102,241,0.88))] p-7 text-white shadow-[0_22px_55px_rgba(67,56,202,0.26)]">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-100">For parents</p>
          <h2 className="mt-3 text-3xl font-semibold">A bedtime story that feels calming and gentle</h2>
          <ul className="mt-5 grid gap-3 text-sm leading-7 text-indigo-50">
            <li>Stories are selected for your child&apos;s age and never repeated to the same inbox.</li>
            <li>Each email opens one secure reader page with no library index or extra app distractions.</li>
            <li>You can unsubscribe instantly from every email we send.</li>
          </ul>
        </div>

        <SignupForm formId="footer-signup" title="Join before launch" compact attribution="lower-page" />
      </section>

      <footer className="mt-10 flex flex-col items-center justify-between gap-3 rounded-[2rem] border border-white/70 bg-white/80 px-5 py-5 text-sm text-slate-600 sm:flex-row">
        <p>Buddybug is currently in pre-launch. Weekly bedtime stories are sent only by email.</p>
        <div className="flex items-center gap-4">
          <Link href="/privacy" className="transition hover:text-indigo-600">
            Privacy
          </Link>
          <Link href="/terms" className="transition hover:text-indigo-600">
            Terms
          </Link>
        </div>
      </footer>
    </div>
  );
}
