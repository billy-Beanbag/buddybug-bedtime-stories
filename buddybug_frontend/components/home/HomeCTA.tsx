"use client";

import Link from "next/link";

import { useAuth } from "@/context/AuthContext";

export function HomeCTA() {
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <section className="relative overflow-hidden rounded-[2.5rem] bg-[linear-gradient(135deg,#1e1b4b,#312e81,#4338ca)] px-6 py-8 text-white shadow-[0_24px_70px_rgba(49,46,129,0.28)] sm:px-8 md:px-10">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.18),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.22),transparent_26%)]" />
      <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-indigo-100">Ready for tonight?</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
            Create your first bedtime routine with Buddybug
          </h2>
          <p className="mt-4 text-base leading-7 text-indigo-50">
            Start with a child profile, open a bedtime pack, and settle into a softer evening reading flow.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            href={isAuthenticated ? "/children" : "/register"}
            className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/15"
          >
            {isLoading ? "Create your first bedtime routine" : isAuthenticated ? "Open child profiles" : "Create your first bedtime routine"}
          </Link>
          <Link
            href={isAuthenticated ? "/library" : "/library"}
            className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white backdrop-blur transition hover:bg-white/15"
          >
            Explore the library
          </Link>
        </div>
      </div>
    </section>
  );
}
