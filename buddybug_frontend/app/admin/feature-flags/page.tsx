"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { FeatureFlagEditor, type FeatureFlagFormValue } from "@/components/admin/FeatureFlagEditor";
import { FeatureFlagTable } from "@/components/admin/FeatureFlagTable";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import type { FeatureFlagRead } from "@/lib/types";

function toPayload(form: FeatureFlagFormValue) {
  return {
    ...form,
    description: form.description || null,
    environments: form.environments || null,
    target_subscription_tiers: form.target_subscription_tiers || null,
    target_languages: form.target_languages || null,
    target_age_bands: form.target_age_bands || null,
    target_roles: form.target_roles || null,
    target_user_ids: form.target_user_ids || null,
    target_countries: form.target_countries || null,
    target_beta_cohorts: form.target_beta_cohorts || null,
  };
}

export default function AdminFeatureFlagsPage() {
  const { token, isAdmin } = useAuth();
  const [flags, setFlags] = useState<FeatureFlagRead[]>([]);
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlagRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadFlags() {
    if (!token) {
      return;
    }
    setLoading(true);
    setLoadError(null);
    try {
      const response = await apiGet<FeatureFlagRead[]>("/admin/feature-flags", { token });
      setFlags(response);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Unable to load feature flags");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadFlags();
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only admin users can manage feature flags." />;
  }

  if (loading) {
    return <LoadingState message="Loading feature flags..." />;
  }

  if (loadError) {
    return <EmptyState title="Unable to load feature flags" description={loadError} />;
  }

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold text-slate-900">Release management</h2>
        <p className="mt-1 text-sm text-slate-600">
          Use feature flags to stage launches by environment, audience, and rollout percentage without redeploying code.
        </p>
      </section>

      <FeatureFlagEditor
        flag={selectedFlag}
        submitting={saving}
        onSubmit={async (form) => {
          if (!token) {
            return;
          }
          setSaving(true);
          setStatusMessage(null);
          try {
            if (selectedFlag) {
              await apiPatch<FeatureFlagRead>(`/admin/feature-flags/${selectedFlag.id}`, toPayload(form), { token });
            } else {
              await apiPost<FeatureFlagRead>("/admin/feature-flags", toPayload(form), { token });
            }
            setSelectedFlag(null);
            await loadFlags();
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to save feature flag");
          } finally {
            setSaving(false);
          }
        }}
        onCancel={selectedFlag ? () => setSelectedFlag(null) : undefined}
      />

      {statusMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{statusMessage}</div>
      ) : null}

      {flags.length ? (
        <FeatureFlagTable
          flags={flags}
          deletingId={deletingId}
          onEdit={(flag) => setSelectedFlag(flag)}
          onDelete={async (flag) => {
            if (!token) {
              return;
            }
            setDeletingId(flag.id);
            setStatusMessage(null);
            try {
              await apiDelete<void>(`/admin/feature-flags/${flag.id}`, { token });
              if (selectedFlag?.id === flag.id) {
                setSelectedFlag(null);
              }
              await loadFlags();
            } catch (err) {
              setStatusMessage(err instanceof Error ? err.message : "Unable to delete feature flag");
            } finally {
              setDeletingId(null);
            }
          }}
        />
      ) : (
        <EmptyState
          title="No feature flags yet"
          description="Create the first release flag to start staging Buddybug changes more safely."
        />
      )}
    </div>
  );
}
