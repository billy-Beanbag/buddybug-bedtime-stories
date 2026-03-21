"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import type { AdminAnalyticsBookStat, AnalyticsFunnelResponse, AnalyticsSummaryResponse } from "@/lib/types";

export default function AdminAnalyticsPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [funnel, setFunnel] = useState<AnalyticsFunnelResponse | null>(null);
  const [books, setBooks] = useState<AdminAnalyticsBookStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    async function loadAnalytics() {
      setLoading(true);
      setError(null);
      try {
        const [summaryResponse, funnelResponse, booksResponse] = await Promise.all([
          apiGet<AnalyticsSummaryResponse>("/admin/analytics/summary", { token }),
          apiGet<AnalyticsFunnelResponse>("/admin/analytics/funnel", { token }),
          apiGet<AdminAnalyticsBookStat[]>("/admin/analytics/books", { token }),
        ]);
        setSummary(summaryResponse);
        setFunnel(funnelResponse);
        setBooks(booksResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load analytics");
      } finally {
        setLoading(false);
      }
    }

    void loadAnalytics();
  }, [token]);

  if (loading) {
    return <LoadingState message="Loading analytics..." />;
  }

  if (error || !summary || !funnel) {
    return <EmptyState title="Unable to load analytics" description={error || "Analytics data is unavailable."} />;
  }

  const funnelEntries = Object.entries(funnel);

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-xl font-semibold text-slate-900">Analytics summary</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">Total events</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.total_events}</p>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">Unique users</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.unique_users}</p>
          </div>
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-slate-500">Unique readers</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{summary.unique_readers}</p>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900">Funnel</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {funnelEntries.map(([label, value]) => (
            <div key={label} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">{label.replaceAll("_", " ")}</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900">Top books</h2>
        <div className="mt-4 space-y-3">
          {books.length ? (
            books.map((book) => (
              <div key={book.book_id} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-base font-semibold text-slate-900">{book.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">Book #{book.book_id}</p>
                  </div>
                  <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700">
                    Total {book.total}
                  </span>
                </div>
                <div className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-5">
                  <span>Opens: {book.opens}</span>
                  <span>Completions: {book.completions}</span>
                  <span>Replays: {book.replays}</span>
                  <span>Audio starts: {book.audio_starts}</span>
                  <span>Recommendation clicks: {book.recommendation_clicks}</span>
                </div>
              </div>
            ))
          ) : (
            <EmptyState title="No book analytics yet" description="Tracked book engagement will appear here." />
          )}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold text-slate-900">Top event counts</h2>
        <div className="mt-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
            {Object.entries(summary.top_event_counts).map(([eventName, count]) => (
              <div key={eventName} className="flex items-center justify-between rounded-2xl bg-slate-50 px-3 py-2">
                <span>{eventName}</span>
                <span className="font-medium text-slate-900">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
