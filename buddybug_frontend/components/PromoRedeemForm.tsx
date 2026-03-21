"use client";

import { useState } from "react";

interface PromoRedeemFormProps {
  submitting?: boolean;
  onSubmit: (code: string) => Promise<void>;
}

export function PromoRedeemForm({ submitting = false, onSubmit }: PromoRedeemFormProps) {
  const [code, setCode] = useState("");

  return (
    <form
      className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(code);
      }}
    >
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Redeem a promo or partner code</h2>
        <p className="mt-1 text-sm text-slate-600">
          Enter a Buddybug partnership or pilot code to unlock temporary access on your account.
        </p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Promo code</span>
        <input
          type="text"
          value={code}
          onChange={(event) => setCode(event.target.value.toUpperCase())}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          placeholder="PARTNER2026"
          required
          disabled={submitting}
        />
      </label>

      <button
        type="submit"
        disabled={submitting || !code.trim()}
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-medium text-slate-900 disabled:opacity-60"
      >
        {submitting ? "Redeeming..." : "Redeem code"}
      </button>
    </form>
  );
}
