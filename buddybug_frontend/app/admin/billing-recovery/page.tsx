"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { BillingRecoveryCaseTable } from "@/components/admin/BillingRecoveryCaseTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type { BillingRecoveryCaseRead } from "@/lib/types";

export default function AdminBillingRecoveryPage() {
  const { token, isAdmin } = useAuth();
  const [cases, setCases] = useState<BillingRecoveryCaseRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    async function loadCases() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiGet<BillingRecoveryCaseRead[]>("/admin/billing-recovery/cases", {
          token,
          query: { limit: 100 },
        });
        setCases(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load billing recovery queue");
      } finally {
        setLoading(false);
      }
    }

    void loadCases();
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage billing recovery follow-up." />;
  }

  if (loading) {
    return <LoadingState message="Loading billing recovery queue..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load billing recovery queue" description={error} />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Billing recovery queue</h1>
        <p className="mt-2 text-sm text-slate-600">
          Track families with premium billing trouble, review recovery history, and resolve cases once premium is healthy again.
        </p>
      </section>

      {cases.length ? (
        <BillingRecoveryCaseTable cases={cases} />
      ) : (
        <EmptyState
          title="No billing recovery cases right now"
          description="Open Stripe billing trouble cases will appear here when a premium renewal needs follow-up."
        />
      )}
    </div>
  );
}
