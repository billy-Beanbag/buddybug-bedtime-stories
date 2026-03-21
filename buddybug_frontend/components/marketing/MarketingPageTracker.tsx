"use client";

import { useEffect } from "react";

import { useAuth } from "@/context/AuthContext";
import { useLocale } from "@/context/LocaleContext";
import { trackMarketingPageViewed } from "@/lib/analytics";

export function MarketingPageTracker({
  eventName,
  source,
}: {
  eventName:
    | "marketing_home_viewed"
    | "marketing_pricing_viewed"
    | "marketing_features_viewed"
    | "marketing_faq_viewed";
  source: string;
}) {
  const { token, user } = useAuth();
  const { locale } = useLocale();

  useEffect(() => {
    void trackMarketingPageViewed({
      eventName,
      source,
      token,
      user,
      language: locale,
    });
  }, [eventName, locale, source, token, user]);

  return null;
}
