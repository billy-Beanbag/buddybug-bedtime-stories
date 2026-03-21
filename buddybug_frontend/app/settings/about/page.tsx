"use client";

import Link from "next/link";
import { useEffect } from "react";

import { AboutAppCard } from "@/components/AboutAppCard";
import { AppSectionCard } from "@/components/AppSectionCard";
import { useAuth } from "@/context/AuthContext";
import { useLocale } from "@/context/LocaleContext";
import { trackAboutOpened } from "@/lib/analytics";

export default function SettingsAboutPage() {
  const { token, user } = useAuth();
  const { locale } = useLocale();

  useEffect(() => {
    void trackAboutOpened({ token, user, language: locale });
  }, [locale, token, user]);

  return (
    <div className="space-y-4">
      <AboutAppCard language={locale} />
      <AppSectionCard title="Need help?">
        <Link
          href="/support"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
        >
          Open support
        </Link>
      </AppSectionCard>
    </div>
  );
}
