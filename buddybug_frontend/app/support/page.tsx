"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppSectionCard } from "@/components/AppSectionCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { SupportTicketForm } from "@/components/SupportTicketForm";
import { SupportTicketList } from "@/components/SupportTicketList";
import { useAuth } from "@/context/AuthContext";
import { SUPPORT_EMAIL } from "@/lib/app-config";
import { apiGet, apiPost } from "@/lib/api";
import type { SupportTicketListResponse, SupportTicketRead } from "@/lib/types";

const helpTopics = [
  {
    title: "Account and billing help",
    description: "Questions about upgrading, checkout, Premium access, or billing portal issues.",
  },
  {
    title: "Story playback help",
    description: "Reader, narration, preview, and page playback issues for web or app experiences.",
  },
  {
    title: "Parental controls help",
    description: "Questions about bedtime mode, age filtering, autoplay, or child-specific restrictions.",
  },
  {
    title: "Downloads and offline help",
    description: "Trouble with saved books, offline-ready packages, or missing downloads.",
  },
  {
    title: "Premium access help",
    description: "Feature access questions around audio, full stories, premium voices, and family personalization.",
  },
];

export default function SupportPage() {
  const { token, user, isAuthenticated } = useAuth();
  const [tickets, setTickets] = useState<SupportTicketRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadTickets() {
    if (!token || !isAuthenticated) {
      setTickets([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<SupportTicketListResponse>("/support/me", { token });
      setTickets(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load support requests");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTickets();
  }, [isAuthenticated, token]);

  return (
    <div className="space-y-5">
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Help & support</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Reach the Buddybug team for bugs, billing help, content concerns, feature requests, and family support questions.
        </p>
      </section>

      <section className="grid gap-3">
        {helpTopics.map((item) => (
          <div key={item.title} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="font-semibold text-slate-900">{item.title}</h3>
            <p className="mt-1 text-sm text-slate-600">{item.description}</p>
          </div>
        ))}
      </section>

      <AppSectionCard title="Contact options" description="Use in-app tickets for tracked support, or email the team for account and device help.">
        <div className="grid gap-3 sm:grid-cols-2">
          <a
            href={`mailto:${SUPPORT_EMAIL}`}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
          >
            Email {SUPPORT_EMAIL}
          </a>
          <Link
            href="/settings/about"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center text-sm font-medium text-slate-900"
          >
            About Buddybug
          </Link>
        </div>
      </AppSectionCard>

      <SupportTicketForm
        isAuthenticated={isAuthenticated}
        initialEmail={user?.email || ""}
        onSubmit={async (payload) => {
          await apiPost("/support/tickets", payload, token ? { token } : undefined);
          await loadTickets();
        }}
      />

      {isAuthenticated ? (
        <section className="space-y-3">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">My support requests</h3>
            <p className="mt-1 text-sm text-slate-600">Track the requests you have already submitted to the Buddybug team.</p>
          </div>
          {loading ? (
            <LoadingState message="Loading support requests..." />
          ) : error ? (
            <EmptyState title="Unable to load support requests" description={error} />
          ) : tickets.length ? (
            <SupportTicketList tickets={tickets} />
          ) : (
            <EmptyState title="No support requests yet" description="Your submitted support requests will appear here." />
          )}
        </section>
      ) : null}
    </div>
  );
}
