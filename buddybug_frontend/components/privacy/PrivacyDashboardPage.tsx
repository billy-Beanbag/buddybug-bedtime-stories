"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { DataRequestForm } from "@/components/DataRequestForm";
import { DataRequestList } from "@/components/DataRequestList";
import { EmptyState } from "@/components/EmptyState";
import { LegalAcceptanceStatus } from "@/components/LegalAcceptanceStatus";
import { LoadingState } from "@/components/LoadingState";
import { PrivacyPreferencesForm } from "@/components/PrivacyPreferencesForm";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { DataRequestRead, LegalAcceptanceRead, PrivacyDashboardResponse, PrivacyPreferenceRead } from "@/lib/types";

export function PrivacyDashboardPage() {
  const { token, isAuthenticated, isLoading } = useAuth();
  const { childProfiles } = useChildProfiles();
  const [dashboard, setDashboard] = useState<PrivacyDashboardResponse | null>(null);
  const [preferences, setPreferences] = useState<PrivacyPreferenceRead | null>(null);
  const [requests, setRequests] = useState<DataRequestRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [submittingRequest, setSubmittingRequest] = useState(false);
  const [accepting, setAccepting] = useState<"terms" | "privacy" | null>(null);

  async function loadPrivacyState() {
    if (!token) {
      return;
    }
    setLoading(true);
    setLoadError(null);
    try {
      const [dashboardResponse, preferencesResponse, requestsResponse] = await Promise.all([
        apiGet<PrivacyDashboardResponse>("/privacy/me", { token }),
        apiGet<PrivacyPreferenceRead>("/privacy/me/preferences", { token }),
        apiGet<DataRequestRead[]>("/privacy/me/data-requests", { token }),
      ]);
      setDashboard(dashboardResponse);
      setPreferences(preferencesResponse);
      setRequests(requestsResponse);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Unable to load privacy dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token) {
      return;
    }
    void loadPrivacyState();
  }, [token]);

  if (isLoading || loading) {
    return <LoadingState message="Loading privacy controls..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to manage privacy"
          description="Privacy preferences, legal acceptance history, and data requests are available for authenticated parent accounts."
        />
        <div className="grid gap-3 sm:grid-cols-2">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Create account
          </Link>
        </div>
      </div>
    );
  }

  if (loadError || !dashboard) {
    return <EmptyState title="Unable to load privacy dashboard" description={loadError || "Privacy data is unavailable."} />;
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-3xl font-semibold text-slate-900">Privacy & Data</h1>
        <p className="mt-2 text-sm text-slate-600">
          Review legal acceptance history, adjust privacy settings, and request account or child data exports or deletions.
        </p>
      </section>

      {statusMessage ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {statusMessage}
        </div>
      ) : null}
      {actionError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {actionError}
        </div>
      ) : null}

      <LegalAcceptanceStatus
        termsAcceptance={dashboard.latest_terms_acceptance}
        privacyAcceptance={dashboard.latest_privacy_acceptance}
        accepting={accepting}
        onAcceptTerms={async () => {
          setAccepting("terms");
          setStatusMessage(null);
          setActionError(null);
          try {
            const acceptance = await apiPost<LegalAcceptanceRead>("/privacy/me/accept/terms", undefined, { token });
            setDashboard((current) =>
              current
                ? {
                    ...current,
                    latest_terms_acceptance: acceptance,
                  }
                : current,
            );
            setStatusMessage("Terms acceptance recorded.");
          } catch (err) {
            setActionError(err instanceof Error ? err.message : "Unable to record terms acceptance");
          } finally {
            setAccepting(null);
          }
        }}
        onAcceptPrivacy={async () => {
          setAccepting("privacy");
          setStatusMessage(null);
          setActionError(null);
          try {
            const acceptance = await apiPost<LegalAcceptanceRead>("/privacy/me/accept/privacy", undefined, { token });
            setDashboard((current) =>
              current
                ? {
                    ...current,
                    latest_privacy_acceptance: acceptance,
                  }
                : current,
            );
            setStatusMessage("Privacy policy acceptance recorded.");
          } catch (err) {
            setActionError(err instanceof Error ? err.message : "Unable to record privacy acceptance");
          } finally {
            setAccepting(null);
          }
        }}
      />

      <PrivacyPreferencesForm
        preferences={preferences}
        saving={savingPreferences}
        onSubmit={async (value) => {
          setSavingPreferences(true);
          setStatusMessage(null);
          setActionError(null);
          try {
            const updated = await apiPatch<PrivacyPreferenceRead>("/privacy/me/preferences", value, { token });
            setPreferences(updated);
            setDashboard((current) =>
              current
                ? {
                    ...current,
                    privacy_preference: updated,
                  }
                : current,
            );
            setStatusMessage("Privacy preferences updated.");
          } catch (err) {
            setActionError(err instanceof Error ? err.message : "Unable to update privacy preferences");
          } finally {
            setSavingPreferences(false);
          }
        }}
      />

      <DataRequestForm
        childProfiles={childProfiles}
        submitting={submittingRequest}
        onSubmit={async (value) => {
          setSubmittingRequest(true);
          setStatusMessage(null);
          setActionError(null);
          try {
            const created = await apiPost<DataRequestRead>("/privacy/me/data-requests", value, { token });
            setRequests((current) => [created, ...current]);
            setDashboard((current) =>
              current
                ? {
                    ...current,
                    active_data_requests: [created, ...current.active_data_requests],
                  }
                : current,
            );
            setStatusMessage("Data request submitted.");
          } catch (err) {
            setActionError(err instanceof Error ? err.message : "Unable to submit data request");
          } finally {
            setSubmittingRequest(false);
          }
        }}
      />

      <DataRequestList title="Your data request history" items={requests} />
    </div>
  );
}
