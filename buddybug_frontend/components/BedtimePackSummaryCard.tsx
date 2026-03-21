"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet } from "@/lib/api";
import type { BedtimePackDetailResponse } from "@/lib/types";

interface BedtimePackSummaryCardProps {
  detail?: BedtimePackDetailResponse | null;
  loadLatest?: boolean;
}

export function BedtimePackSummaryCard({ detail: providedDetail = null, loadLatest = false }: BedtimePackSummaryCardProps) {
  const { token, isAuthenticated, isLoading } = useAuth();
  const { selectedChildProfile } = useChildProfiles();
  const [detail, setDetail] = useState<BedtimePackDetailResponse | null>(providedDetail);

  useEffect(() => {
    setDetail(providedDetail);
  }, [providedDetail]);

  useEffect(() => {
    if (!loadLatest || providedDetail || isLoading || !isAuthenticated || !token) {
      return;
    }

    void apiGet<BedtimePackDetailResponse>("/bedtime-packs/me/latest", {
      token,
      query: { child_profile_id: selectedChildProfile?.id },
    })
      .then((response) => setDetail(response))
      .catch(() => setDetail(null));
  }, [isAuthenticated, isLoading, loadLatest, providedDetail, selectedChildProfile?.id, token]);

  const progress = useMemo(() => {
    if (!detail) {
      return { total: 0, completed: 0 };
    }
    const total = detail.items.length;
    const completed = detail.items.filter((item) => item.completion_status === "completed").length;
    return { total, completed };
  }, [detail]);

  if (!detail) {
    return null;
  }

  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-indigo-700">Tonight's Bedtime Pack</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">{detail.pack.title}</h2>
          <p className="mt-2 text-sm text-slate-600">
            {detail.pack.generated_reason || "A calm multi-story session is ready for tonight."}
          </p>
        </div>
        <Link
          href="/bedtime-pack"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Open pack
        </Link>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Stories</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{progress.total}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Completed</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{progress.completed}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3">
          <p className="text-sm text-slate-500">Narration</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{detail.pack.prefer_narration ? "On" : "Off"}</p>
        </div>
      </div>
    </section>
  );
}
