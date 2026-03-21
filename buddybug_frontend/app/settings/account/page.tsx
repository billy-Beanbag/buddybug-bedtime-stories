"use client";

import Link from "next/link";

import { AppSectionCard } from "@/components/AppSectionCard";
import { useAuth } from "@/context/AuthContext";

export default function SettingsAccountPage() {
  const { user, billing, subscription, hasPremiumAccess } = useAuth();

  const tier = billing?.subscription_tier || subscription?.subscription_tier || user?.subscription_tier || "free";
  const status = billing?.subscription_status || subscription?.subscription_status || user?.subscription_status || "none";

  return (
    <div className="space-y-4">
      <AppSectionCard
        title="Account settings"
        description="Identity and subscription stay here so the app shell can keep operational settings separate."
      >
        <dl className="grid gap-3 text-sm">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">Email</dt>
            <dd className="mt-1 font-medium text-slate-900">{user?.email || "Not signed in"}</dd>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">Subscription tier</dt>
            <dd className="mt-1 font-medium text-slate-900">{tier}</dd>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">Subscription status</dt>
            <dd className="mt-1 font-medium text-slate-900">{status}</dd>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">Premium access</dt>
            <dd className="mt-1 font-medium text-slate-900">{hasPremiumAccess ? "Active" : "Not active"}</dd>
          </div>
        </dl>
      </AppSectionCard>

      <AppSectionCard title="Manage account" description="Use the full profile screen for billing, language, growth, and account actions.">
        <Link
          href="/profile"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
        >
          Open profile
        </Link>
      </AppSectionCard>
    </div>
  );
}
