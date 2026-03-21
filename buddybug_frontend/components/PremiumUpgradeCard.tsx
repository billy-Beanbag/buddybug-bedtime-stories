"use client";

import { useEffect, useRef, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import {
  trackMessageVariantClicked,
  trackMessageVariantExposed,
} from "@/lib/analytics";
import { fetchMessageExperimentBundle } from "@/lib/message-experiments";
import type { MessageExperimentSurfaceCopy } from "@/lib/types";

export function PremiumUpgradeCard({
  onUpgrade,
  loading = false,
}: {
  onUpgrade: () => void;
  loading?: boolean;
}) {
  const { token, user } = useAuth();
  const [copy, setCopy] = useState<MessageExperimentSurfaceCopy | null>(null);
  const exposureTracked = useRef(false);

  useEffect(() => {
    void fetchMessageExperimentBundle({ token, user }).then((bundle) => setCopy(bundle.upgrade_card));
  }, [token, user]);

  useEffect(() => {
    if (!copy || exposureTracked.current) {
      return;
    }
    exposureTracked.current = true;
    void trackMessageVariantExposed("premium_upgrade_card", {
      token,
      user,
      experimentKey: copy.experiment_key,
      experimentVariant: copy.variant,
      source: "premium_upgrade_card",
    });
  }, [copy, token, user]);

  return (
    <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#1e1b4b,#312e81,#4338ca)] p-5 text-white shadow-[0_24px_60px_rgba(49,46,129,0.22)]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.16),transparent_28%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.18),transparent_26%)]" />
      <div className="relative">
      <h3 className="text-xl font-semibold text-white">
        {copy?.title || "Upgrade when Buddybug becomes part of your routine"}
      </h3>
      <p className="mt-2 text-sm leading-6 text-indigo-50">
        {copy?.description ||
          "Premium is $9.99 and includes unlimited stories, full library access, bedtime packs, narration voices, unlimited child profiles, and personalised recommendations."}
      </p>
      <button
        type="button"
        onClick={() => {
          void trackMessageVariantClicked("premium_upgrade_card", {
            token,
            user,
            experimentKey: copy?.experiment_key,
            experimentVariant: copy?.variant,
            source: "premium_upgrade_card",
            target: "/profile",
          });
          onUpgrade();
        }}
        disabled={loading}
        className="mt-4 w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 font-medium text-white backdrop-blur disabled:opacity-60"
      >
        {loading ? "Opening checkout..." : copy?.cta_label || "Upgrade to Premium"}
      </button>
      </div>
    </section>
  );
}
