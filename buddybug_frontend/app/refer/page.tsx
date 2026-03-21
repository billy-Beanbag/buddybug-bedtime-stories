"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ReferralCard } from "@/components/ReferralCard";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type { ReferralSummaryResponse } from "@/lib/types";

export default function ReferPage() {
  const { isAuthenticated, isLoading, token } = useAuth();
  const [summary, setSummary] = useState<ReferralSummaryResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setSummary(null);
      return;
    }
    void apiGet<ReferralSummaryResponse>("/growth/referral/me", { token })
      .then((response) => {
        setSummary(response);
        setLoadError(null);
      })
      .catch((err) => setLoadError(err instanceof Error ? err.message : "Unable to load referral summary"));
  }, [isAuthenticated, token]);

  if (isLoading) {
    return <LoadingState message="Loading your referral code..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to refer Buddybug"
          description="Referral codes are tied to your Buddybug account so signups can be attributed correctly."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link href="/login" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900">
            Login
          </Link>
          <Link href="/register" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900">
            Register
          </Link>
        </div>
      </div>
    );
  }

  if (loadError) {
    return <EmptyState title="Referral summary unavailable" description={loadError} />;
  }

  if (!summary) {
    return <LoadingState message="Preparing your referral summary..." />;
  }

  return (
    <div className="space-y-4">
      <ReferralCard summary={summary} />
      <div className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600">
        Referral rewards stay lightweight in this foundation stage. Buddybug now tracks invites, attributed signups, and later premium conversions.
      </div>
    </div>
  );
}
