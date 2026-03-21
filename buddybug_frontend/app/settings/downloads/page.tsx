"use client";

import { useEffect, useState } from "react";

import { AppSectionCard } from "@/components/AppSectionCard";
import { DownloadsSummaryCard } from "@/components/DownloadsSummaryCard";
import { useAuth } from "@/context/AuthContext";
import { useConnectivity } from "@/context/ConnectivityContext";
import { useLocale } from "@/context/LocaleContext";
import { trackDownloadsSettingsOpened } from "@/lib/analytics";
import { fetchSavedLibrary } from "@/lib/library";
import { listOfflineBookPackages } from "@/lib/offline-storage";

export default function SettingsDownloadsPage() {
  const { token, user } = useAuth();
  const { locale } = useLocale();
  const { pendingSyncCount } = useConnectivity();
  const [savedCount, setSavedCount] = useState(0);
  const [offlineCount, setOfflineCount] = useState(0);

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

  useEffect(() => {
    async function loadOfflineCount() {
      try {
        const offlinePackages = await listOfflineBookPackages();
        setOfflineCount(offlinePackages.length);
      } catch {
        setOfflineCount(0);
      }
    }

    void loadOfflineCount();
    function handleOfflinePackagesChanged() {
      void loadOfflineCount();
    }
    window.addEventListener("buddybug:offline-packages-changed", handleOfflinePackagesChanged as EventListener);
    return () => {
      window.removeEventListener("buddybug:offline-packages-changed", handleOfflinePackagesChanged as EventListener);
    };
  }, []);

  return (
    <div className="space-y-4">
      <DownloadsSummaryCard offlineCount={offlineCount} savedCount={savedCount} />
      <AppSectionCard
        title="Sync status"
        description="Offline progress and download state can queue locally and sync when the connection returns."
      >
        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Pending sync actions: <span className="font-medium text-slate-900">{pendingSyncCount}</span>
        </div>
      </AppSectionCard>
    </div>
  );
}
