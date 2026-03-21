"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { AddBetaMemberForm, type AddBetaMemberValue } from "@/components/admin/AddBetaMemberForm";
import { BetaMembershipTable } from "@/components/admin/BetaMembershipTable";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { BetaCohortDetailResponse, BetaCohortMembershipRead } from "@/lib/types";

export default function AdminBetaCohortDetailPage({ params }: { params: { cohortId: string } }) {
  const cohortId = Number(params.cohortId);
  const { token, isAdmin } = useAuth();
  const [detail, setDetail] = useState<BetaCohortDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [addingMember, setAddingMember] = useState(false);
  const [updatingMembershipId, setUpdatingMembershipId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadDetail() {
    if (!token || !cohortId) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await apiGet<BetaCohortDetailResponse>(`/admin/beta-cohorts/${cohortId}`, { token });
      setDetail(response);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load beta cohort details");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token && cohortId) {
      void loadDetail();
    }
  }, [token, cohortId]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage beta cohort memberships." />;
  }

  if (loading) {
    return <LoadingState message="Loading beta cohort..." />;
  }

  if (!detail) {
    return <EmptyState title="Beta cohort not found" description="The requested cohort could not be loaded." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">{detail.cohort.name}</h1>
        <p className="mt-2 text-sm text-slate-600">{detail.cohort.description || "No description provided yet."}</p>
        <div className="mt-3 flex flex-wrap gap-3 text-sm text-slate-600">
          <span className="rounded-full bg-slate-100 px-3 py-1 font-mono text-xs text-slate-700">{detail.cohort.key}</span>
          <span>{detail.cohort.is_active ? "Active cohort" : "Inactive cohort"}</span>
          <span>Feature flags: {detail.cohort.feature_flag_keys || "None listed"}</span>
        </div>
      </section>

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <section className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Members</h2>
            <p className="mt-1 text-sm text-slate-600">Activate or deactivate access without losing the membership record.</p>
          </div>
          {detail.memberships.length ? (
            <BetaMembershipTable
              memberships={detail.memberships}
              updatingMembershipId={updatingMembershipId}
              onToggleActive={async (membership: BetaCohortMembershipRead, nextActive: boolean) => {
                if (!token) {
                  return;
                }
                setUpdatingMembershipId(membership.id);
                setStatusMessage(null);
                setErrorMessage(null);
                try {
                  await apiPatch(`/admin/beta-cohort-memberships/${membership.id}`, { is_active: nextActive }, { token });
                  setStatusMessage(`${nextActive ? "Reactivated" : "Deactivated"} membership for user #${membership.user_id}.`);
                  await loadDetail();
                } catch (err) {
                  setErrorMessage(err instanceof Error ? err.message : "Unable to update membership");
                } finally {
                  setUpdatingMembershipId(null);
                }
              }}
            />
          ) : (
            <EmptyState title="No members yet" description="Add the first user to start a controlled preview." />
          )}
        </section>

        <AddBetaMemberForm
          submitting={addingMember}
          onSubmit={async (value: AddBetaMemberValue) => {
            if (!token) {
              return;
            }
            setAddingMember(true);
            setStatusMessage(null);
            setErrorMessage(null);
            try {
              await apiPost(`/admin/beta-cohorts/${cohortId}/members`, value, { token });
              setStatusMessage(`Added user #${value.user_id} to ${detail.cohort.name}.`);
              await loadDetail();
            } catch (err) {
              setErrorMessage(err instanceof Error ? err.message : "Unable to add beta member");
            } finally {
              setAddingMember(false);
            }
          }}
        />
      </div>
    </div>
  );
}
