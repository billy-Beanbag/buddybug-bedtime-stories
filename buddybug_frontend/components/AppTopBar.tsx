"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { ChildProfileSwitcher } from "@/components/ChildProfileSwitcher";
import { useAuth } from "@/context/AuthContext";
import { trackAppShellNavigationUsed, trackLanguageChanged } from "@/lib/analytics";
import { APP_NAME } from "@/lib/app-config";
import { LOCALE_LABELS, SUPPORTED_LOCALES } from "@/lib/i18n";
import { useLocale } from "@/context/LocaleContext";

const ROOT_TITLES: Record<string, string> = {
  "/library": "Library",
  "/continue-reading": "Continue Reading",
  "/saved": "Saved Books",
  "/story-suggestions": "Story Suggestions",
  "/profile": "Profile",
  "/settings": "Settings",
  "/support": "Support",
  "/notifications": "Notifications",
  "/children": "Family",
  "/achievements": "Achievements",
  "/family-digest": "Family Digest",
  "/bedtime-pack": "Bedtime Pack",
  "/reading-plans": "Reading Plans",
  "/privacy": "Privacy & Data",
  "/parental-controls": "Parental Controls",
  "/gifts": "Gift Buddybug",
  "/refer": "Refer a Friend",
  "/upgrade": "Upgrade",
  "/onboarding": "Welcome",
};

function getScreenTitle(pathname: string) {
  if (ROOT_TITLES[pathname]) {
    return ROOT_TITLES[pathname];
  }
  if (pathname.startsWith("/reader/")) {
    return "Reader";
  }
  if (pathname.startsWith("/reading-plans/")) {
    return "Reading Plan";
  }
  if (pathname.startsWith("/bedtime-pack/")) {
    return "Bedtime Pack";
  }
  if (pathname.startsWith("/children/") && pathname.endsWith("/comfort")) {
    return "Comfort Preferences";
  }
  if (pathname.startsWith("/settings/account")) {
    return "Account";
  }
  if (pathname.startsWith("/settings/family")) {
    return "Family";
  }
  if (pathname.startsWith("/settings/privacy")) {
    return "Privacy";
  }
  if (pathname.startsWith("/settings/notifications")) {
    return "Notifications";
  }
  if (pathname.startsWith("/settings/downloads")) {
    return "Saved Library";
  }
  if (pathname.startsWith("/settings/about")) {
    return "About";
  }
  if (pathname.startsWith("/settings")) {
    return "Settings";
  }
  if (pathname.startsWith("/onboarding/child")) {
    return "Child Setup";
  }
  if (pathname.startsWith("/onboarding/preferences")) {
    return "Preferences";
  }
  if (pathname.startsWith("/onboarding/bedtime")) {
    return "Bedtime Setup";
  }
  if (pathname.startsWith("/onboarding/first-story")) {
    return "First Story";
  }
  if (pathname.startsWith("/onboarding")) {
    return "Welcome";
  }
  return APP_NAME;
}

function shouldShowBack(pathname: string) {
  return (
    pathname.startsWith("/reader/") ||
    pathname.startsWith("/settings/") ||
    pathname.startsWith("/onboarding/") ||
    pathname.startsWith("/children/")
  );
}

const MENU_NAV_ITEMS = [
  { href: "/children", label: "Family" },
  { href: "/profile", label: "Profile" },
  { href: "/bedtime-pack", label: "Bedtime Pack" },
  { href: "/story-suggestions", label: "Story Suggestions" },
  { href: "/support", label: "Support" },
];

export function AppTopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const { locale, setLocale, t } = useLocale();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  return (
    <header className="mb-5 rounded-[1.75rem] border border-white/70 bg-white/84 px-4 py-3 shadow-sm backdrop-blur supports-[padding:max(0px)]:pt-[max(0.75rem,env(safe-area-inset-top))]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {shouldShowBack(pathname) ? (
              <button
                type="button"
                onClick={() => {
                  void trackAppShellNavigationUsed("back_button", { source: pathname });
                  router.back();
                }}
                className="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900"
              >
                Back
              </button>
            ) : null}
            <div>
              <p className="text-[11px] uppercase tracking-[0.2em] text-slate-500">{APP_NAME}</p>
              <h1 className="truncate text-base font-semibold text-slate-900 sm:text-lg">{getScreenTitle(pathname)}</h1>
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setMenuOpen((current) => !current)}
          className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-900"
          aria-expanded={menuOpen}
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
        >
          <span className="flex flex-col gap-1">
            <span className="block h-0.5 w-5 rounded-full bg-slate-900" />
            <span className="block h-0.5 w-5 rounded-full bg-slate-900" />
            <span className="block h-0.5 w-5 rounded-full bg-slate-900" />
          </span>
        </button>
      </div>

      {isAuthenticated ? (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200/80 pt-3">
          <p className="rounded-full border border-indigo-100 bg-indigo-50/80 px-3 py-1.5 text-xs font-semibold text-indigo-800">
            Reading profile
          </p>
          <div className="min-w-[220px] max-w-sm flex-1">
            <ChildProfileSwitcher />
          </div>
        </div>
      ) : null}

      {menuOpen ? (
        <div className="mt-4 space-y-4 border-t border-slate-200 pt-4">
          <nav className="grid gap-2">
            {MENU_NAV_ITEMS.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === item.href
                  : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => {
                    void trackAppShellNavigationUsed(item.href, { source: "app_top_menu" });
                  }}
                  className={`rounded-2xl px-4 py-3 text-sm font-medium transition ${
                    isActive
                      ? "border border-indigo-200 bg-indigo-50 text-indigo-950"
                      : "border border-slate-200 bg-white text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="grid gap-3">
            <label className="text-xs text-slate-600">
              <span className="mb-1 block">{t("languageLabel")}</span>
              <select
                value={locale}
                onChange={(event) => {
                  const nextLocale = event.target.value;
                  void trackLanguageChanged(nextLocale, {
                    previousLanguage: locale,
                    source: "app_top_bar",
                  });
                  setLocale(nextLocale);
                }}
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none"
              >
                {SUPPORTED_LOCALES.map((option) => (
                  <option key={option} value={option}>
                    {LOCALE_LABELS[option]}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      ) : null}
    </header>
  );
}
