"use client";

import { useState } from "react";

import type { GiftSubscriptionRead } from "@/lib/types";

interface GiftListProps {
  gifts: GiftSubscriptionRead[];
}

export function GiftList({ gifts }: GiftListProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  async function handleCopy(code: string) {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(code);
      window.setTimeout(() => setCopiedCode(null), 1500);
    } catch {
      setCopiedCode(null);
    }
  }

  if (!gifts.length) {
    return (
      <div className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
        No gifts yet. Create a code to send Buddybug premium to another family.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {gifts.map((gift) => (
        <div key={gift.id} className="rounded-[2rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">Gift code</div>
              <div className="mt-2 text-xl font-semibold tracking-[0.12em] text-slate-900">{gift.code}</div>
              <p className="mt-2 text-sm text-slate-600">
                {gift.duration_days} days • {gift.status}
                {gift.notes ? ` • ${gift.notes}` : ""}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleCopy(gift.code)}
              className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900"
            >
              {copiedCode === gift.code ? "Copied" : "Copy code"}
            </button>
          </div>

          <div className="mt-3 text-sm text-slate-600">
            Purchased {new Date(gift.purchased_at).toLocaleString()}
            {gift.redeemed_at ? ` • Redeemed ${new Date(gift.redeemed_at).toLocaleString()}` : ""}
            {gift.expires_at ? ` • Access ends ${new Date(gift.expires_at).toLocaleString()}` : ""}
          </div>
        </div>
      ))}
    </div>
  );
}
