"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { GiftList } from "@/components/GiftList";
import { GiftRedemptionForm } from "@/components/GiftRedemptionForm";
import { GiftSubscriptionForm } from "@/components/GiftSubscriptionForm";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { GiftSubscriptionRead, GiftSubscriptionRedeemResponse } from "@/lib/types";

export default function GiftsPage() {
  const { isAuthenticated, isLoading, token, refreshMe, refreshSubscription, refreshBilling } = useAuth();
  const [gifts, setGifts] = useState<GiftSubscriptionRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [redeeming, setRedeeming] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadGifts() {
    if (!token) {
      return;
    }
    setLoading(true);
    try {
      const response = await apiGet<GiftSubscriptionRead[]>("/growth/gifts/me", { token });
      setGifts(response);
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Unable to load gifts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token || !isAuthenticated) {
      setGifts([]);
      setLoading(false);
      return;
    }
    void loadGifts();
  }, [isAuthenticated, token]);

  if (isLoading || (isAuthenticated && loading)) {
    return <LoadingState message="Loading gifts..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to create or redeem gifts"
          description="Gift subscriptions are linked to Buddybug accounts so premium access can be applied safely."
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
      <GiftSubscriptionForm
        submitting={creating}
        onSubmit={async (value) => {
          if (!token) {
            return;
          }
          setCreating(true);
          setStatusMessage(null);
          try {
            await apiPost<GiftSubscriptionRead>("/growth/gifts", value, { token });
            await loadGifts();
            setStatusMessage("Gift code created.");
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to create gift");
          } finally {
            setCreating(false);
          }
        }}
      />

      <GiftRedemptionForm
        submitting={redeeming}
        onSubmit={async (code) => {
          if (!token) {
            return;
          }
          setRedeeming(true);
          setStatusMessage(null);
          try {
            const response = await apiPost<GiftSubscriptionRedeemResponse>("/growth/gifts/redeem", { code }, { token });
            await Promise.all([loadGifts(), refreshMe(), refreshSubscription(), refreshBilling()]);
            setStatusMessage(
              response.expires_at
                ? `Gift redeemed. Premium access is active until ${new Date(response.expires_at).toLocaleString()}.`
                : "Gift redeemed.",
            );
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to redeem gift");
          } finally {
            setRedeeming(false);
          }
        }}
      />

      {statusMessage ? (
        <div className="rounded-[2rem] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">{statusMessage}</div>
      ) : null}

      {loadError ? <EmptyState title="Gift history unavailable" description={loadError} /> : <GiftList gifts={gifts} />}
    </div>
  );
}
