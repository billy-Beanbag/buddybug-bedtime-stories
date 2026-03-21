"use client";

import { useEffect, useMemo, useState } from "react";

import { BreakdownList } from "@/components/admin/BreakdownList";
import { ContentPerformanceTable } from "@/components/admin/ContentPerformanceTable";
import { KPICard } from "@/components/admin/KPICard";
import { ReportingFilters, type ReportingFilterState } from "@/components/admin/ReportingFilters";
import { SupportMetricsCard } from "@/components/admin/SupportMetricsCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type {
  ContentPerformanceResponse,
  EngagementMetricsResponse,
  KPIOverviewResponse,
  SegmentBreakdownResponse,
  SubscriptionMetricsResponse,
  SupportMetricsResponse,
} from "@/lib/types";

export default function AdminReportingPage() {
  const { token, isAdmin } = useAuth();
  const [filters, setFilters] = useState<ReportingFilterState>({ days: "30", startDate: "", endDate: "" });
  const [overview, setOverview] = useState<KPIOverviewResponse | null>(null);
  const [engagement, setEngagement] = useState<EngagementMetricsResponse | null>(null);
  const [subscriptions, setSubscriptions] = useState<SubscriptionMetricsResponse | null>(null);
  const [content, setContent] = useState<ContentPerformanceResponse | null>(null);
  const [languages, setLanguages] = useState<SegmentBreakdownResponse | null>(null);
  const [ageBands, setAgeBands] = useState<SegmentBreakdownResponse | null>(null);
  const [contentLanes, setContentLanes] = useState<SegmentBreakdownResponse | null>(null);
  const [supportMetrics, setSupportMetrics] = useState<SupportMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo(
    () => ({
      days: filters.days || undefined,
      start_date: filters.startDate || undefined,
      end_date: filters.endDate || undefined,
    }),
    [filters.days, filters.endDate, filters.startDate],
  );

  async function loadDashboard() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [
        overviewResponse,
        engagementResponse,
        subscriptionsResponse,
        contentResponse,
        languagesResponse,
        ageBandsResponse,
        contentLanesResponse,
        supportResponse,
      ] = await Promise.all([
        apiGet<KPIOverviewResponse>("/admin/reporting/kpi-overview", { token, query }),
        apiGet<EngagementMetricsResponse>("/admin/reporting/engagement", { token, query }),
        apiGet<SubscriptionMetricsResponse>("/admin/reporting/subscriptions", { token, query }),
        apiGet<ContentPerformanceResponse>("/admin/reporting/content/top", { token, query: { ...query, limit: 20 } }),
        apiGet<SegmentBreakdownResponse>("/admin/reporting/breakdown/languages", { token, query }),
        apiGet<SegmentBreakdownResponse>("/admin/reporting/breakdown/age-bands", { token, query }),
        apiGet<SegmentBreakdownResponse>("/admin/reporting/breakdown/content-lanes", { token, query }),
        apiGet<SupportMetricsResponse>("/admin/reporting/support", { token, query }),
      ]);
      setOverview(overviewResponse);
      setEngagement(engagementResponse);
      setSubscriptions(subscriptionsResponse);
      setContent(contentResponse);
      setLanguages(languagesResponse);
      setAgeBands(ageBandsResponse);
      setContentLanes(contentLanesResponse);
      setSupportMetrics(supportResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load reporting dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, [token, query]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only admin users can open executive reporting." />;
  }

  if (loading) {
    return <LoadingState message="Loading executive reporting..." />;
  }

  if (
    error ||
    !overview ||
    !engagement ||
    !subscriptions ||
    !content ||
    !languages ||
    !ageBands ||
    !contentLanes ||
    !supportMetrics
  ) {
    return <EmptyState title="Unable to load reporting dashboard" description={error || "Reporting data is unavailable."} />;
  }

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-xl font-semibold text-slate-900">Executive reporting</h2>
        <p className="mt-1 text-sm text-slate-600">Monitor families, subscriptions, engagement, content performance, and support load.</p>
        <div className="mt-4">
          <ReportingFilters value={filters} onChange={setFilters} />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900">Top KPIs</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <KPICard label="Total users" value={overview.total_users} />
          <KPICard label="Active users" value={overview.active_users_30d} hint="Window-based activity" />
          <KPICard label="Child profiles" value={overview.total_child_profiles} />
          <KPICard label="Premium users" value={overview.total_premium_users} hint={`${overview.premium_conversion_rate}% conversion`} />
          <KPICard label="Published books" value={overview.total_published_books} />
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KPICard label="Saved items" value={overview.total_saved_library_items} />
          <KPICard label="Downloads" value={overview.total_downloads} />
          <KPICard label="Open support tickets" value={overview.total_support_tickets_open} />
          <KPICard
            label="Generated at"
            value={new Date(overview.generated_at).toLocaleString()}
            hint="Latest reporting snapshot"
          />
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="grid gap-4 sm:grid-cols-2">
          <KPICard label="Book opens" value={engagement.book_opens_30d} />
          <KPICard label="Book completions" value={engagement.book_completions_30d} />
          <KPICard label="Book replays" value={engagement.book_replays_30d} />
          <KPICard label="Narration starts" value={engagement.narration_starts_30d} />
          <KPICard label="Narration completions" value={engagement.narration_completions_30d} />
          <KPICard label="Daily story usage" value={engagement.daily_story_views_30d} />
          <KPICard label="Completion rate" value={`${engagement.avg_completion_rate_30d}%`} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <KPICard label="Free users" value={subscriptions.free_users} />
          <KPICard label="Premium users" value={subscriptions.premium_users} />
          <KPICard label="Trialing users" value={subscriptions.trialing_users} />
          <KPICard label="Canceled users" value={subscriptions.canceled_users} />
          <KPICard label="Checkout started" value={subscriptions.checkout_started_30d} />
          <KPICard label="Checkout completed" value={subscriptions.checkout_completed_30d} />
          <KPICard label="Active conversion" value={`${subscriptions.active_conversion_rate}%`} />
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900">Top content</h2>
        <div className="mt-4">
          {content.items.length ? (
            <ContentPerformanceTable items={content.items} />
          ) : (
            <EmptyState title="No content metrics yet" description="Book activity will appear here once families start reading." />
          )}
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-4">
        <BreakdownList title="Languages" items={languages.items} />
        <BreakdownList title="Age bands" items={ageBands.items} />
        <BreakdownList title="Content lanes" items={contentLanes.items} />
        <SupportMetricsCard metrics={supportMetrics} />
      </section>
    </div>
  );
}
