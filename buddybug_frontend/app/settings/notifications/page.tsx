"use client";

import Link from "next/link";

import { AppSectionCard } from "@/components/AppSectionCard";

export default function SettingsNotificationsPage() {
  return (
    <div className="space-y-4">
      <AppSectionCard
        title="Notification settings"
        description="Notification controls stay reachable from one stable settings route for future packaged-app navigation."
      >
        <p className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
          Manage bedtime reminders, daily stories, and reading alerts from the existing notifications screen.
        </p>
      </AppSectionCard>

      <AppSectionCard title="Open notifications">
        <Link
          href="/notifications"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
        >
          Open notifications
        </Link>
      </AppSectionCard>
    </div>
  );
}
