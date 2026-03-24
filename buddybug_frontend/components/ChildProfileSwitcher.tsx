"use client";

import Link from "next/link";

import { useChildProfiles } from "@/context/ChildProfileContext";

export function ChildProfileSwitcher() {
  const { childProfiles, selectedChildProfile, setSelectedChildProfile } = useChildProfiles();

  if (!childProfiles.length) {
    return (
      <Link
        href="/children"
        className="inline-flex rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700"
      >
        Add child profile
      </Link>
    );
  }

  return (
    <label className="block text-xs text-slate-600">
      <span className="mb-1 block">Reading for</span>
      <select
        value={selectedChildProfile?.id ?? ""}
        onChange={(event) =>
          setSelectedChildProfile(event.target.value ? Number(event.target.value) : null)
        }
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none"
      >
        <option value="">All library books</option>
        {childProfiles.map((profile) => (
          <option key={profile.id} value={profile.id}>
            {profile.display_name} ({profile.age_band})
          </option>
        ))}
      </select>
    </label>
  );
}
