"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { AdminCommandPalette } from "@/components/admin/AdminCommandPalette";
import { useFeatureFlags } from "@/context/FeatureFlagsContext";

type AdminLink = { href: string; label: string; flagKey?: string };

const primaryAdminLinks: AdminLink[] = [
  { href: "/admin", label: "Dashboard" },
  { href: "/admin/workflow", label: "Workflow" },
  { href: "/admin/ideas", label: "Ideas" },
  { href: "/admin/drafts", label: "Drafts" },
  { href: "/admin/story-pages", label: "Story Pages" },
  { href: "/admin/books", label: "Books" },
  { href: "/admin/illustrations", label: "Image Queue" },
];

const secondaryAdminLinks: AdminLink[] = [
  { href: "/admin/search", label: "Search Console" },
  { href: "/admin/editorial", label: "Editorial", flagKey: "editorial_tools_enabled" },
  { href: "/admin/story-quality", label: "Story Quality" },
  { href: "/admin/visual-references", label: "Visual References" },
  { href: "/admin/translations", label: "Translations" },
  { href: "/admin/audio", label: "Audio" },
  { href: "/admin/support", label: "Support" },
  { href: "/admin/moderation", label: "Moderation" },
  { href: "/admin/incidents", label: "Incidents" },
  { href: "/admin/runbooks", label: "Runbooks" },
  { href: "/admin/maintenance", label: "Maintenance" },
  { href: "/admin/housekeeping", label: "Housekeeping" },
  { href: "/admin/status", label: "Public Status" },
  { href: "/admin/billing-recovery", label: "Billing Recovery" },
  { href: "/admin/reporting", label: "Reporting" },
  { href: "/admin/api-keys", label: "API Keys" },
  { href: "/admin/account-health", label: "Account Health" },
  { href: "/admin/organization", label: "Organization" },
  { href: "/admin/beta", label: "Beta Cohorts" },
  { href: "/admin/feature-flags", label: "Feature Flags" },
  { href: "/admin/changelog", label: "Changelog" },
];

export function AdminNav() {
  const pathname = usePathname();
  const { isEnabled } = useFeatureFlags();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [showMoreTools, setShowMoreTools] = useState(false);
  const visiblePrimaryLinks = primaryAdminLinks.filter((link) => !link.flagKey || isEnabled(link.flagKey));
  const visibleSecondaryLinks = secondaryAdminLinks.filter((link) => !link.flagKey || isEnabled(link.flagKey));

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "k") {
        return;
      }
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      const isEditable =
        tagName === "input" ||
        tagName === "textarea" ||
        tagName === "select" ||
        Boolean(target?.isContentEditable);
      if (isEditable) {
        return;
      }
      event.preventDefault();
      setPaletteOpen(true);
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <>
      <nav className="rounded-3xl border border-slate-200 bg-white p-3 shadow-sm">
        <button
          type="button"
          onClick={() => setPaletteOpen(true)}
          className="mb-3 flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900"
        >
          <span>Search</span>
          <span className="rounded-xl border border-slate-200 bg-white px-2 py-1 text-xs text-slate-500">Ctrl/Cmd+K</span>
        </button>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
          {visiblePrimaryLinks.map((link) => {
            const isActive =
              link.href === "/admin"
                ? pathname === link.href
                : pathname === link.href || pathname.startsWith(`${link.href}/`);

            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-2xl border px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "border-indigo-200 bg-indigo-50 text-indigo-900 shadow-sm"
                    : "border-transparent text-slate-700 hover:border-slate-200 hover:bg-slate-100"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        <div className="mt-4 border-t border-slate-100 pt-4">
          <button
            type="button"
            onClick={() => setShowMoreTools((current) => !current)}
            className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-900"
          >
            <span>More tools</span>
            <span className="text-xs text-slate-500">{showMoreTools ? "Hide" : "Show"}</span>
          </button>

          {showMoreTools ? (
            <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
              {visibleSecondaryLinks.map((link) => {
                const isActive =
                  link.href === "/admin"
                    ? pathname === link.href
                    : pathname === link.href || pathname.startsWith(`${link.href}/`);

                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`rounded-2xl border px-4 py-3 text-sm font-medium transition ${
                      isActive
                        ? "border-indigo-200 bg-indigo-50 text-indigo-900 shadow-sm"
                        : "border-transparent text-slate-700 hover:border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </div>
          ) : (
            <p className="mt-3 px-1 text-xs leading-5 text-slate-500">
              Advanced tools, reporting, maintenance, and support pages are tucked away here.
            </p>
          )}
        </div>
      </nav>
      <AdminCommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </>
  );
}
