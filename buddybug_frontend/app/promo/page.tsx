"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { PromoRedeemForm } from "@/components/PromoRedeemForm";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { PromoAccessRedeemResponse, PromoAccessRedemptionRead } from "@/lib/types";

export default function PromoPage() {
  const { isAuthenticated, isLoading, token, refreshMe, refreshSubscription, refreshBilling } = useAuth();
  const [redemptions, setRedemptions] = useState<PromoAccessRedemptionRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [redeeming, setRedeeming] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadRedemptions() {
    if (!token) {
      return;
    }
    setLoading(true);
    try {
      const response = await apiGet<PromoAccessRedemptionRead[]>("/promo/me/redemptions", { token });
      setRedemptions(response);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Unable to load promo redemptions");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setRedemptions([]);
      setLoading(false);
      return;
    }
    void loadRedemptions();
  }, [isAuthenticated, token]);

  if (isLoading || (isAuthenticated && loading)) {
    return <LoadingState message="Loading promo access..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to redeem a promo code"
          description="Partner and promotional access is applied to a Buddybug account so access changes can be tracked safely."
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

  return (
    <div className="space-y-4">
      <PromoRedeemForm
        submitting={redeeming}
        onSubmit={async (code) => {
          if (!token) {
            return;
          }
          setRedeeming(true);
          setStatusMessage(null);
          try {
            const response = await apiPost<PromoAccessRedeemResponse>("/promo/redeem", { code }, { token });
            await Promise.all([loadRedemptions(), refreshMe(), refreshSubscription(), refreshBilling()]);
            setStatusMessage(
              response.expires_at
                ? `Promo redeemed. ${response.code.name} is active until ${new Date(response.expires_at).toLocaleString()}.`
                : `Promo redeemed. ${response.code.name} has been applied to your account.`,
            );
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to redeem promo code");
          } finally {
            setRedeeming(false);
          }
        }}
      />

      {statusMessage ? (
        <div className="rounded-[2rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">{statusMessage}</div>
      ) : null}

      {loadError ? (
        <EmptyState title="Promo history unavailable" description={loadError} />
      ) : (
        <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">Your promo redemptions</h2>
            <p className="mt-1 text-sm text-slate-600">A simple history of redeemed partner or promotional access codes.</p>
          </div>
          {redemptions.length ? (
            <div className="grid gap-3">
              {redemptions.map((redemption) => (
                <div key={redemption.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm text-slate-700">
                  <p className="font-medium text-slate-900">Redemption #{redemption.id}</p>
                  <p className="mt-1">Redeemed at {new Date(redemption.redeemed_at).toLocaleString()}</p>
                  <p className="mt-1">
                    {redemption.expires_at
                      ? `Access expires ${new Date(redemption.expires_at).toLocaleString()}`
                      : "No promo expiry was recorded for this redemption."}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No promo codes redeemed yet"
              description="Redeemed pilot and partner offers will appear here after they are applied to your account."
            />
          )}
        </section>
      )}
    </div>
  );
}
