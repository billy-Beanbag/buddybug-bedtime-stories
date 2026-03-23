"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { NextActionsList } from "@/components/admin/NextActionsList";
import { PipelineCountCard } from "@/components/admin/PipelineCountCard";
import { useAuth } from "@/context/AuthContext";
import { useFeatureFlags } from "@/context/FeatureFlagsContext";
import { apiGet } from "@/lib/api";
import { ADMIN_CARD_HOVER } from "@/lib/admin-styles";
import type { AdminNextActionsResponse, PipelineCountsResponse } from "@/lib/types";

type QuickLink = { href: string; label: string; flagKey?: string };

const primaryQuickLinks: QuickLink[] = [
  { href: "/admin/workflow", label: "Workflow" },
  { href: "/admin/ideas", label: "Ideas" },
  { href: "/admin/drafts", label: "Drafts" },
  { href: "/admin/story-pages", label: "Story Pages" },
  { href: "/admin/books", label: "Books" },
  { href: "/admin/illustrations", label: "Image Queue" },
];

const secondaryQuickLinks: QuickLink[] = [
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
  { href: "/admin/feature-flags", label: "Feature Flags" },
  { href: "/admin/beta", label: "Beta Cohorts" },
  { href: "/admin/changelog", label: "Changelog" },
  { href: "/admin/analytics", label: "Analytics" },
];

export default function AdminDashboardPage() {
  const { token } = useAuth();
  const { isEnabled } = useFeatureFlags();
  const [counts, setCounts] = useState<PipelineCountsResponse | null>(null);
  const [actions, setActions] = useState<AdminNextActionsResponse | null>(null);
  const [showAllStats, setShowAllStats] = useState(false);
  const [showMoreShortcuts, setShowMoreShortcuts] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const [pipelineCounts, nextActions] = await Promise.all([
          apiGet<PipelineCountsResponse>("/admin/pipeline-counts", { token }),
          apiGet<AdminNextActionsResponse>("/admin/next-actions", { token }),
        ]);
        setCounts(pipelineCounts);
        setActions(nextActions);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load admin dashboard");
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, [token]);

  const priorityCountEntries = useMemo(
    () =>
      counts
        ? ([
            ["Drafts pending review", counts.draft_pending_review],
            ["Prompt-ready pages", counts.story_pages_prompt_ready],
            ["Illustrations waiting", counts.illustrations_generated],
            ["Books ready", counts.books_ready],
            ["Published books", counts.books_published],
            ["Needs revision", counts.needs_revision],
          ] as const)
        : [],
    [counts],
  );

  if (loading) {
    return <LoadingState message="Loading admin dashboard..." />;
  }

  if (error || !counts || !actions) {
    return <EmptyState title="Unable to load dashboard" description={error || "Dashboard data is unavailable."} />;
  }

  const countEntries = [
    ["Ideas pending", counts.idea_pending],
    ["Drafts pending review", counts.draft_pending_review],
    ["Needs revision", counts.needs_revision],
    ["Approved for illustration", counts.approved_for_illustration],
    ["Prompt-ready pages", counts.story_pages_prompt_ready],
    ["Illustrations waiting", counts.illustrations_generated],
    ["Books ready", counts.books_ready],
    ["Published books", counts.books_published],
    ["Audio waiting", counts.audio_generated],
  ] as const;
  const visiblePrimaryQuickLinks = primaryQuickLinks.filter((link) => !link.flagKey || isEnabled(link.flagKey));
  const visibleSecondaryQuickLinks = secondaryQuickLinks.filter((link) => !link.flagKey || isEnabled(link.flagKey));
  const urgentActionCount = priorityCountEntries
    .filter(([label]) => label !== "Published books")
    .reduce((total, [, count]) => total + count, 0);

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-white/80 bg-white/90 p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">Today&apos;s focus</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">Keep story production moving</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Use the workflow as the main production surface. Review drafts, check preview books in context, and only
              drop into support queues when something needs manual help.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/admin/workflow"
              className="rounded-2xl bg-indigo-600 px-4 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-500"
            >
              Open workflow
            </Link>
            <Link
              href="/admin/drafts"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
            >
              Review drafts
            </Link>
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <div className="rounded-3xl border border-indigo-100 bg-indigo-50/70 p-4">
            <p className="text-sm font-medium text-indigo-900">Urgent workflow items</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{urgentActionCount}</p>
            <p className="mt-2 text-sm text-indigo-900">Review-ready drafts, waiting pages, image decisions, and books ready to publish.</p>
          </div>
          <div className="rounded-3xl border border-emerald-100 bg-emerald-50/70 p-4">
            <p className="text-sm font-medium text-emerald-900">Published books</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{counts.books_published}</p>
            <p className="mt-2 text-sm text-emerald-900">Stories already live in the reader app.</p>
          </div>
          <div className="rounded-3xl border border-amber-100 bg-amber-50/70 p-4">
            <p className="text-sm font-medium text-amber-900">Needs revision</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{counts.needs_revision}</p>
            <p className="mt-2 text-sm text-amber-900">Drafts that need another editing pass before continuing.</p>
          </div>
        </div>
      </section>

      <section>
        <div className="flex items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Pipeline snapshot</h2>
            <p className="mt-1 text-sm text-slate-600">The most useful counters stay visible first.</p>
          </div>
          <button
            type="button"
            onClick={() => setShowAllStats((current) => !current)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900 shadow-sm"
          >
            {showAllStats ? "Show fewer stats" : "Show all stats"}
          </button>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {(showAllStats ? countEntries : priorityCountEntries).map(([label, count]) => (
            <PipelineCountCard key={label} label={label} count={count} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900">Next actions</h2>
        <p className="mt-1 text-sm text-slate-600">The workflow items that likely need attention first.</p>
        <div className="mt-4">
          <NextActionsList items={actions.items} />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900">Quick navigation</h2>
        <p className="mt-1 text-sm text-slate-600">Keep the main production areas close at hand.</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {visiblePrimaryQuickLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-3xl border border-slate-200 bg-white p-4 text-base font-medium text-slate-900 shadow-sm ${ADMIN_CARD_HOVER}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <button
            type="button"
            onClick={() => setShowMoreShortcuts((current) => !current)}
            className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-900"
          >
            <span>More admin areas</span>
            <span className="text-xs text-slate-500">{showMoreShortcuts ? "Hide" : "Show"}</span>
          </button>

          {showMoreShortcuts ? (
            <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {visibleSecondaryQuickLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`rounded-3xl border border-slate-200 bg-white p-4 text-base font-medium text-slate-900 shadow-sm ${ADMIN_CARD_HOVER}`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-600">
              Reporting, maintenance, support, and advanced tools are tucked away here to keep the dashboard lighter.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}
