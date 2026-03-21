"use client";

import Link from "next/link";
import { useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiPost } from "@/lib/api";
import type { CheckoutSessionResponse } from "@/lib/types";

export function UpgradePageContent() {
  const { token, isAuthenticated, isLoading, hasPremiumAccess } = useAuth();
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  const [upgradeError, setUpgradeError] = useState<string | null>(null);

  async function handleUpgrade() {
    if (!token) {
      return;
    }

    setUpgradeLoading(true);
    setUpgradeError(null);
    try {
      const response = await apiPost<CheckoutSessionResponse>(
        "/billing/checkout",
        { price_key: "premium_monthly" },
        { token },
      );
      window.location.assign(response.checkout_url);
    } catch (err) {
      setUpgradeError(err instanceof Error ? err.message : "Unable to open checkout");
      setUpgradeLoading(false);
    }
  }

  if (isLoading) {
    return <LoadingState message="Loading upgrade options..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to view upgrade options"
          description="Upgrade is available from inside a Buddybug account. You can still review the public pricing page first."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/pricing"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            View pricing
          </Link>
          <Link href="/login" className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white">
            Log in
          </Link>
        </div>
      </div>
    );
  }

  if (hasPremiumAccess) {
    return (
      <div className="space-y-4">
        <section className="rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-emerald-100">Premium active</p>
          <h2 className="mt-3 text-3xl font-semibold">You already have full Buddybug access</h2>
          <p className="mt-3 text-sm leading-6 text-indigo-50">
            Premium is active on your account, so you already have unlimited stories, full library access, bedtime packs,
            narration voices, downloadable offline stories, unlimited child profiles, and personalised recommendations.
          </p>
        </section>
        <div className="grid gap-3 sm:grid-cols-2">
          <Link
            href="/profile"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Manage account
          </Link>
          <Link href="/library" className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white">
            Back to library
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-indigo-100">Upgrade</p>
        <h2 className="mt-3 text-3xl font-semibold">Unlock the full Buddybug experience</h2>
        <p className="mt-3 text-sm leading-6 text-indigo-50">
          Premium is designed for families who want Buddybug to become part of a real bedtime routine, without weekly
          limits or locked features getting in the way.
        </p>
        <div className="mt-5 rounded-2xl border border-white/10 bg-white/10 px-4 py-4">
          <p className="text-sm font-medium text-indigo-100">Premium</p>
          <p className="mt-2 text-4xl font-semibold text-white">$9.99</p>
          <p className="mt-2 text-sm text-indigo-50">per month</p>
        </div>
      </section>

      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <h3 className="text-xl font-semibold text-slate-900">What changes when you upgrade</h3>
        <div className="mt-4 grid gap-3">
          <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <span className="font-medium text-slate-900">Free Plan:</span> 3 stories per week, smaller library, 1 child
            profile, no bedtime packs, no narration voice.
          </div>
          <div className="rounded-2xl border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-950">
            <span className="font-medium">Premium:</span> Unlimited stories, full library access, bedtime packs, narration
            voices, downloadable offline stories, unlimited child profiles, and personalised recommendations.
          </div>
        </div>
      </section>

      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <h3 className="text-xl font-semibold text-slate-900">Premium includes</h3>
        <div className="mt-4 grid gap-2 text-sm text-slate-700">
          {[
            "Unlimited stories",
            "Full library access",
            "Bedtime packs",
            "Narration voices",
            "Downloadable offline stories",
            "Unlimited child profiles",
            "Personalised recommendations",
          ].map((feature) => (
            <p key={feature} className="rounded-2xl bg-slate-50 px-4 py-3">
              {feature}
            </p>
          ))}
        </div>
      </section>

      {upgradeError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{upgradeError}</div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => void handleUpgrade()}
          disabled={upgradeLoading}
          className="rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {upgradeLoading ? "Opening checkout..." : "Upgrade to Premium"}
        </button>
        <Link
          href="/library"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          Maybe later
        </Link>
      </div>
    </div>
  );
}
