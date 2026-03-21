"use client";

import { useState } from "react";

import type { ReferralSummaryResponse } from "@/lib/types";

interface ReferralCardProps {
  summary: ReferralSummaryResponse;
}

export function ReferralCard({ summary }: ReferralCardProps) {
  const [copied, setCopied] = useState(false);

  const referralCode = summary.referral_code?.code || "";
  const shareMessage = referralCode
    ? `Join me on Buddybug with my referral code: ${referralCode}`
    : "Join me on Buddybug";

  async function handleCopy(text: string) {
    if (!text) {
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Refer a parent</h2>
        <p className="mt-1 text-sm text-slate-600">
          Share your Buddybug code with another family. Signups are attributed now, and reward logic can grow later.
        </p>
      </div>

      <div className="rounded-3xl border border-indigo-200 bg-indigo-50 px-5 py-4">
        <div className="text-xs font-medium uppercase tracking-[0.2em] text-indigo-700">Your referral code</div>
        <div className="mt-2 text-3xl font-semibold tracking-[0.2em] text-slate-900">{referralCode || "Pending"}</div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-sm text-slate-500">Total referrals</div>
          <div className="mt-1 text-xl font-semibold text-slate-900">{summary.total_referrals}</div>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <div className="text-sm text-slate-500">Premium conversions</div>
          <div className="mt-1 text-xl font-semibold text-slate-900">{summary.premium_conversions}</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => void handleCopy(referralCode)}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
        >
          {copied ? "Copied" : "Copy code"}
        </button>
        <button
          type="button"
          onClick={() => void handleCopy(shareMessage)}
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Copy invite message
        </button>
      </div>
    </section>
  );
}
