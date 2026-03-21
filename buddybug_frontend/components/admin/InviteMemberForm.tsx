"use client";

import { useState } from "react";

export interface InviteMemberFormValue {
  user_id: number;
  role: string;
}

export function InviteMemberForm({
  submitting,
  onSubmit,
}: {
  submitting: boolean;
  onSubmit: (value: InviteMemberFormValue) => Promise<void>;
}) {
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("editor");

  return (
    <form
      className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit({ user_id: Number(userId), role });
      }}
    >
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Add team member</h2>
        <p className="mt-1 text-sm text-slate-600">
          Add an existing Buddybug user by `user_id`. This keeps the first version manual and operationally simple.
        </p>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">User ID</span>
          <input
            type="number"
            min={1}
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            required
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Role</span>
          <select
            value={role}
            onChange={(event) => setRole(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="owner">Owner</option>
            <option value="admin">Admin</option>
            <option value="editor">Editor</option>
            <option value="analyst">Analyst</option>
            <option value="support">Support</option>
          </select>
        </label>
      </div>
      <button
        type="submit"
        disabled={submitting || !userId}
        className="mt-4 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Adding..." : "Add member"}
      </button>
    </form>
  );
}
