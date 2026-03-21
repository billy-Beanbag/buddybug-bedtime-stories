"use client";

import Link from "next/link";

import type { LegalAcceptanceRead } from "@/lib/types";

function AcceptanceCard({
  title,
  href,
  acceptance,
}: {
  title: string;
  href: string;
  acceptance: LegalAcceptanceRead | null;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="font-medium text-slate-900">{title}</h3>
          <p className="mt-1 text-sm text-slate-600">
            {acceptance
              ? `Accepted version ${acceptance.document_version} on ${new Date(acceptance.accepted_at).toLocaleString()}`
              : "Not yet recorded"}
          </p>
        </div>
        <Link href={href} className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900">
          View
        </Link>
      </div>
      {acceptance ? <p className="mt-2 text-xs text-slate-500">Source: {acceptance.source}</p> : null}
    </div>
  );
}

interface LegalAcceptanceStatusProps {
  termsAcceptance: LegalAcceptanceRead | null;
  privacyAcceptance: LegalAcceptanceRead | null;
  onAcceptTerms: () => Promise<void>;
  onAcceptPrivacy: () => Promise<void>;
  accepting?: "terms" | "privacy" | null;
}

export function LegalAcceptanceStatus({
  termsAcceptance,
  privacyAcceptance,
  onAcceptTerms,
  onAcceptPrivacy,
  accepting = null,
}: LegalAcceptanceStatusProps) {
  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Legal acceptance</h2>
        <p className="mt-1 text-sm text-slate-600">
          Buddybug keeps a versioned record of your current terms and privacy policy acceptance.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <AcceptanceCard title="Terms of Service" href="/terms" acceptance={termsAcceptance} />
        <AcceptanceCard title="Privacy Policy" href="/privacy-policy" acceptance={privacyAcceptance} />
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => void onAcceptTerms()}
          disabled={accepting !== null}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
        >
          {accepting === "terms" ? "Recording..." : "Accept current terms"}
        </button>
        <button
          type="button"
          onClick={() => void onAcceptPrivacy()}
          disabled={accepting !== null}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
        >
          {accepting === "privacy" ? "Recording..." : "Accept current privacy policy"}
        </button>
      </div>
    </section>
  );
}
