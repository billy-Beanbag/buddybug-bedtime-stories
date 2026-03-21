"use client";

import Link from "next/link";

import type { ChildProfileRead } from "@/lib/types";

interface ChildProfileCardProps {
  profile: ChildProfileRead;
  selected: boolean;
  onSelect: (childProfileId: number) => void;
}

export function ChildProfileCard({ profile, selected, onSelect }: ChildProfileCardProps) {
  return (
    <article
      className={`relative overflow-hidden rounded-[2rem] border p-5 shadow-[0_24px_60px_rgba(30,41,59,0.18)] ${
        selected
          ? "border-indigo-200/30 bg-[linear-gradient(135deg,#1e1b4b_0%,#312e81_55%,#4338ca_100%)] text-white"
          : "border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] text-white"
      }`}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.16),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
      <div className="relative">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">{profile.display_name}</h3>
          <p className="mt-1 text-sm text-indigo-100">
            Age {profile.age_band} • {profile.language.toUpperCase()}
          </p>
          <p className="mt-1 text-xs text-indigo-200">
            Lane: {profile.content_lane_key || "auto"}
          </p>
        </div>
        {!profile.is_active ? (
          <span className="rounded-full border border-white/15 bg-white/10 px-2 py-1 text-xs font-medium text-indigo-100">Inactive</span>
        ) : null}
      </div>
      {profile.is_active ? (
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => onSelect(profile.id)}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${
              selected
                ? "border border-white/15 bg-white text-slate-900"
                : "border border-white/15 bg-white/10 text-white"
            }`}
          >
            {selected ? "Selected for reading" : "Use this profile"}
          </button>
          <Link
            href={`/children/${profile.id}/comfort`}
            className={`rounded-2xl px-4 py-3 text-center text-sm font-medium ${
              selected
                ? "border border-white/15 bg-white/10 text-white"
                : "border border-white/15 bg-white/10 text-white"
            }`}
          >
            Comfort & Story Preferences
          </Link>
        </div>
      ) : null}
      </div>
    </article>
  );
}
