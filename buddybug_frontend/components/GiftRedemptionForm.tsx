"use client";

import { useState } from "react";

interface GiftRedemptionFormProps {
  submitting?: boolean;
  onSubmit: (code: string) => Promise<void>;
}

export function GiftRedemptionForm({ submitting = false, onSubmit }: GiftRedemptionFormProps) {
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
        <h2 className="text-2xl font-semibold text-slate-900">Redeem a gift</h2>
        <p className="mt-1 text-sm text-slate-600">
          Paste a Buddybug gift code to add premium access to your account.
        </p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Gift code</span>
        <input
          type="text"
          value={code}
          onChange={(event) => setCode(event.target.value.toUpperCase())}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          placeholder="ABCD1234EF"
          required
          disabled={submitting}
        />
      </label>

      <button
        type="submit"
        disabled={submitting || !code.trim()}
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-medium text-slate-900 disabled:opacity-60"
      >
        {submitting ? "Redeeming..." : "Redeem gift"}
      </button>
    </form>
  );
}
