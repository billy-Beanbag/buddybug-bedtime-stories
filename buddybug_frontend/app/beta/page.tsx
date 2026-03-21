"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type { UserBetaAccessResponse } from "@/lib/types";

export default function BetaAccessPage() {
  const { token, isAuthenticated } = useAuth();
  const [betaAccess, setBetaAccess] = useState<UserBetaAccessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadBetaAccess() {
      if (!token) {
        return;
      }
      setLoading(true);
      setErrorMessage(null);
      try {
        const response = await apiGet<UserBetaAccessResponse>("/beta/me", { token });
        setBetaAccess(response);
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "Unable to load beta access");
      } finally {
        setLoading(false);
      }
    }

    if (token) {
      void loadBetaAccess();
    }
  }, [token]);

  if (!isAuthenticated) {
    return <EmptyState title="Login required" description="Sign in to see your Buddybug beta access." />;
  }

  if (loading) {
    return <LoadingState message="Loading beta access..." />;
  }

  if (errorMessage) {
    return <EmptyState title="Unable to load beta access" description={errorMessage} />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Your beta access</h1>
        <p className="mt-2 text-sm text-slate-600">
          Buddybug uses small beta cohorts to preview unfinished features before a wider rollout.
        </p>
      </section>

      {betaAccess && betaAccess.cohorts.length ? (
        <div className="grid gap-4">
          {betaAccess.cohorts.map((cohort) => (
            <section key={cohort.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">{cohort.name}</h2>
              <p className="mt-2 text-sm text-slate-600">{cohort.description || "No description available yet."}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="rounded-full bg-slate-100 px-3 py-1 font-mono text-xs text-slate-700">{cohort.key}</span>
                {cohort.feature_flag_keys ? (
                  <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
                    Flags: {cohort.feature_flag_keys}
                  </span>
                ) : null}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <EmptyState title="No beta access yet" description="Your account is not currently enrolled in any active Buddybug beta cohorts." />
      )}
    </div>
  );
}
