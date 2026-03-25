"use client";

import { useEffect, useMemo, useState } from "react";

import { AppSectionCard } from "@/components/AppSectionCard";
import { AppSettingsList } from "@/components/AppSettingsList";
import { DownloadsSummaryCard } from "@/components/DownloadsSummaryCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useLocale } from "@/context/LocaleContext";
import { trackSettingsOpened } from "@/lib/analytics";
import { fetchSavedLibrary } from "@/lib/library";

export default function SettingsPage() {
  const { token, user } = useAuth();
  const { childProfiles } = useChildProfiles();
  const { locale } = useLocale();
  const [savedCount, setSavedCount] = useState(0);

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
          href: "/saved",
          title: "Saved Library",
          description: "Stories saved to your Buddybug account for easy access later.",
          badge: savedCount ? `${savedCount} saved` : null,
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
    [childProfiles.length, savedCount, user?.subscription_tier],
  );

  return (
    <div className="space-y-4">
      <AppSectionCard
        title="Settings"
        description="A packaging-ready home for family controls, saved stories, privacy, and future wrapped-app settings."
      >
        <AppSettingsList items={settingsItems} />
      </AppSectionCard>
      <DownloadsSummaryCard savedCount={savedCount} />
    </div>
  );
}
