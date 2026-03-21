"use client";

import { useState } from "react";

import { apiPost } from "@/lib/api";
import type { BedtimePackGenerateResponse } from "@/lib/types";

interface GenerateBedtimePackButtonProps {
  token: string | null;
  childProfileId?: number | null;
  label?: string;
  onGenerated?: (response: BedtimePackGenerateResponse) => Promise<void> | void;
}

export function GenerateBedtimePackButton({
  token,
  childProfileId = null,
  label = "Generate tonight's pack",
  onGenerated,
}: GenerateBedtimePackButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<BedtimePackGenerateResponse>(
        "/bedtime-packs/me/generate",
        {
          child_profile_id: childProfileId,
        },
        { token },
      );
      await onGenerated?.(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate bedtime pack");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => void handleClick()}
        disabled={!token || loading}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {loading ? "Preparing..." : label}
      </button>
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
    </div>
  );
}
