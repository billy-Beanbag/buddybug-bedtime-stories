"use client";

import Link from "next/link";

import { AppSectionCard } from "@/components/AppSectionCard";
import { APP_NAME, APP_ENV, APP_VERSION, SUPPORT_EMAIL } from "@/lib/app-config";
import { getPlatformLabel } from "@/lib/platform";

interface AboutAppCardProps {
  language?: string;
}

export function AboutAppCard({ language }: AboutAppCardProps) {
  return (
    <AppSectionCard
      title={`About ${APP_NAME}`}
      description="Packaging readiness keeps the current PWA healthy while preparing Buddybug for future wrapper-based app distribution."
    >
      <dl className="grid gap-3 text-sm">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <dt className="text-slate-500">Version</dt>
          <dd className="mt-1 font-medium text-slate-900">{APP_VERSION}</dd>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <dt className="text-slate-500">Environment</dt>
          <dd className="mt-1 font-medium text-slate-900">{APP_ENV}</dd>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <dt className="text-slate-500">Platform</dt>
          <dd className="mt-1 font-medium text-slate-900">{getPlatformLabel()}</dd>
        </div>
        {language ? (
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">Language</dt>
            <dd className="mt-1 font-medium text-slate-900">{language.toUpperCase()}</dd>
          </div>
        ) : null}
      </dl>
      <div className="grid gap-3">
        <a
          href={`mailto:${SUPPORT_EMAIL}`}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
        >
          Email support
        </a>
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/privacy-policy"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
          >
            Privacy policy
          </Link>
          <Link
            href="/terms"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
          >
            Terms
          </Link>
        </div>
      </div>
    </AppSectionCard>
  );
}
