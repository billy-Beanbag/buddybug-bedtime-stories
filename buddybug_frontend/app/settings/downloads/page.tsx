"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppSectionCard } from "@/components/AppSectionCard";
import { DownloadsSummaryCard } from "@/components/DownloadsSummaryCard";
import { useAuth } from "@/context/AuthContext";
import { useLocale } from "@/context/LocaleContext";
import { trackDownloadsSettingsOpened } from "@/lib/analytics";
import { fetchSavedLibrary } from "@/lib/library";

export default function SettingsDownloadsPage() {
  const { token, user } = useAuth();
  const { locale } = useLocale();
  const [savedCount, setSavedCount] = useState(0);

  useEffect(() => {
    void trackDownloadsSettingsOpened({ token, user, language: locale });
  }, [locale, token, user]);

  useEffect(() => {
    if (!token) {
      setSavedCount(0);
      return;
    }
    void fetchSavedLibrary({ token, status: "saved" })
      .then((response) => setSavedCount(response.items.length))
      .catch(() => setSavedCount(0));
  }, [token]);

  return (
    <div className="space-y-4">
      <DownloadsSummaryCard savedCount={savedCount} />
      <AppSectionCard
        title="Saved stories"
        description="Use your saved library to keep favourite stories easy to find inside your Buddybug account."
      >
        <Link
          href="/saved"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
        >
          Open Saved Books
        </Link>
      </AppSectionCard>
    </div>
  );
}
