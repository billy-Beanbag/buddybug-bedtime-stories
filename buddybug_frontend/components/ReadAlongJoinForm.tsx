"use client";

import { useState } from "react";

export function ReadAlongJoinForm({
  disabled = false,
  loading = false,
  onJoin,
  buttonLabel = "Join session",
}: {
  disabled?: boolean;
  loading?: boolean;
  onJoin: (joinCode: string) => Promise<void> | void;
  buttonLabel?: string;
}) {
  const [joinCode, setJoinCode] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = joinCode.trim().toUpperCase();
    if (!normalized || disabled || loading) {
      return;
    }
    await onJoin(normalized);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
      <input
        type="text"
        value={joinCode}
        onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
        placeholder="Enter join code"
        maxLength={6}
        disabled={disabled || loading}
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm uppercase tracking-[0.18em] text-slate-900 outline-none disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || loading || !joinCode.trim()}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {loading ? "Joining..." : buttonLabel}
      </button>
    </form>
  );
}
