"use client";

import { useEffect, useMemo, useState } from "react";

import { AppSectionCard } from "@/components/AppSectionCard";
import { AppSettingsList } from "@/components/AppSettingsList";
import { DownloadsSummaryCard } from "@/components/DownloadsSummaryCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useConnectivity } from "@/context/ConnectivityContext";
import { useLocale } from "@/context/LocaleContext";
import { trackSettingsOpened } from "@/lib/analytics";
import { fetchSavedLibrary } from "@/lib/library";
import { listOfflineBookPackages } from "@/lib/offline-storage";

export default function SettingsPage() {
  const { token, user } = useAuth();
  const { childProfiles } = useChildProfiles();
  const { locale } = useLocale();
  const { pendingSyncCount } = useConnectivity();
  const [savedCount, setSavedCount] = useState(0);
  const [offlineCount, setOfflineCount] = useState(0);

  useEffect(() => {
    void trackSettingsOpened({ token, user, language: locale });
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

  const settingsItems = useMemo(
    () => {
      const items = [
        {
          href: "/settings/account",
          title: "Account",
          description: "Profile, subscription, language, and sign-in details.",
          badge: user?.subscription_tier || null,
        },
      ];

      if (user?.subscription_tier !== "premium") {
        items.push({
          href: "/upgrade",
          title: "Upgrade",
          description: "Compare the Free Plan and Premium whenever you are ready.",
          badge: null,
        });
      }

      items.push(
        {
          href: "/settings/family",
          title: "Family",
          description: "Child profiles, parental controls, and family reading context.",
          badge: childProfiles.length ? `${childProfiles.length} profiles` : "No profiles",
        },
        {
          href: "/settings/privacy",
          title: "Privacy & Data",
          description: "Consent history, preferences, and export or deletion requests.",
          badge: null,
        },
        {
          href: "/settings/notifications",
          title: "Notifications",
          description: "Bedtime reminders, daily stories, and alerts.",
          badge: null,
        },
        {
          href: "/settings/downloads",
          title: "Downloads",
          description: "Saved books, offline copies, and queued sync actions.",
          badge: offlineCount ? `${offlineCount} offline` : pendingSyncCount ? `${pendingSyncCount} syncing` : null,
        },
        {
          href: "/promo",
          title: "Redeem Code",
          description: "Apply partner, pilot, or promotional access codes to your account.",
          badge: null,
        },
        {
          href: "/settings/about",
          title: "About & Support",
          description: "App version, environment, support details, and legal links.",
          badge: null,
        },
      );

      return items;
    },
    [childProfiles.length, offlineCount, pendingSyncCount, user?.subscription_tier],
  );

  return (
    <div className="space-y-4">
      <AppSectionCard
        title="Settings"
        description="A packaging-ready home for family controls, downloads, privacy, and future wrapped-app settings."
      >
        <AppSettingsList items={settingsItems} />
      </AppSectionCard>
      <DownloadsSummaryCard offlineCount={offlineCount} savedCount={savedCount} />
    </div>
  );
}
