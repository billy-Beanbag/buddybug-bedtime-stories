"use client";

import { useState } from "react";

interface GiftSubscriptionFormProps {
  submitting?: boolean;
  onSubmit: (value: { duration_days: number; notes?: string }) => Promise<void>;
}

const DURATION_OPTIONS = [
  { value: 30, label: "30 days" },
  { value: 90, label: "90 days" },
  { value: 365, label: "365 days" },
];

export function GiftSubscriptionForm({ submitting = false, onSubmit }: GiftSubscriptionFormProps) {
  const [durationDays, setDurationDays] = useState(90);
  const [notes, setNotes] = useState("");

  return (
    <form
      className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit({ duration_days: durationDays, notes: notes || undefined });
      }}
    >
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Create a gift</h2>
        <p className="mt-1 text-sm text-slate-600">
          Generate a shareable Buddybug gift code for another family. Payment checkout can plug in later.
        </p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Gift duration</span>
        <select
          value={durationDays}
          onChange={(event) => setDurationDays(Number(event.target.value))}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={submitting}
        >
          {DURATION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Note for yourself</span>
        <textarea
          rows={3}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          placeholder="Optional reminder like Birthday gift for Maya"
          disabled={submitting}
        />
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Creating gift..." : "Create gift code"}
      </button>
    </form>
  );
}
