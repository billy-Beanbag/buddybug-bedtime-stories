"use client";

import Link from "next/link";

import { AppSectionCard } from "@/components/AppSectionCard";
import { useChildProfiles } from "@/context/ChildProfileContext";

export default function SettingsFamilyPage() {
  const { childProfiles, selectedChildProfile } = useChildProfiles();

  return (
    <div className="space-y-4">
      <AppSectionCard
        title="Family settings"
        description="Future wrapped apps need a stable family surface for profile selection, age context, and parental controls."
      >
        <dl className="grid gap-3 text-sm">
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">Active child context</dt>
            <dd className="mt-1 font-medium text-slate-900">
              {selectedChildProfile
                ? `${selectedChildProfile.display_name} • ${selectedChildProfile.age_band} • ${selectedChildProfile.language.toUpperCase()}`
                : "No child profile selected"}
            </dd>
          </div>
          <div className="rounded-2xl bg-slate-50 px-4 py-3">
            <dt className="text-slate-500">Active child profiles</dt>
            <dd className="mt-1 font-medium text-slate-900">{childProfiles.length}</dd>
          </div>
        </dl>
      </AppSectionCard>

      <AppSectionCard title="Manage family areas" description="Open the existing family tools from the central settings flow.">
        <div className="grid gap-3">
          <Link
            href="/children"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
          >
            Manage child profiles
          </Link>
          <Link
            href="/parental-controls"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
          >
            Open parental controls
          </Link>
        </div>
      </AppSectionCard>
    </div>
  );
}
