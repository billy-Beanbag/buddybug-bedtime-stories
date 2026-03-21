"use client";

import { useState } from "react";

export interface AddBetaMemberValue {
  user_id: number;
  source: string;
  is_active: boolean;
}

export function AddBetaMemberForm({
  submitting,
  onSubmit,
}: {
  submitting: boolean;
  onSubmit: (value: AddBetaMemberValue) => Promise<void>;
}) {
  const [userId, setUserId] = useState("");
  const [source, setSource] = useState("admin");
  const [isActive, setIsActive] = useState(true);

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit({ user_id: Number(userId), source, is_active: isActive })
          .then(() => {
            setUserId("");
            setSource("admin");
            setIsActive(true);
          })
          .catch(() => {
            // Parent component surfaces request errors.
          });
      }}
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Add beta member</h2>
        <p className="mt-1 text-sm text-slate-600">Assign users directly by Buddybug user ID for controlled early access.</p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">User ID</span>
        <input
          type="number"
          min={1}
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          required
        />
      </label>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Source</span>
        <select
          value={source}
          onChange={(event) => setSource(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        >
          <option value="admin">admin</option>
          <option value="internal">internal</option>
          <option value="migration">migration</option>
          <option value="invite_code">invite_code</option>
        </select>
      </label>

      <label className="flex items-center gap-3 text-sm text-slate-700">
        <input type="checkbox" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />
        Membership active immediately
      </label>

      <button
        type="submit"
        disabled={submitting || !userId.trim()}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Adding..." : "Add member"}
      </button>
    </form>
  );
}
