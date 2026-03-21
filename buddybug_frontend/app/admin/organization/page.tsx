"use client";

import { useEffect, useState } from "react";

import { ActivityFeed } from "@/components/admin/ActivityFeed";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { InviteMemberForm, type InviteMemberFormValue } from "@/components/admin/InviteMemberForm";
import { OrganizationCard } from "@/components/admin/OrganizationCard";
import { OrganizationMembersTable } from "@/components/admin/OrganizationMembersTable";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPatch, apiPost, ApiError } from "@/lib/api";
import type { OrganizationDetailResponse, OrganizationMembershipRead, OrganizationRead } from "@/lib/types";

export default function AdminOrganizationPage() {
  const { token, isAdmin } = useAuth();
  const [detail, setDetail] = useState<OrganizationDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [adding, setAdding] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [removingId, setRemovingId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [orgName, setOrgName] = useState("");
  const [orgSlug, setOrgSlug] = useState("");

  async function loadOrganization() {
    if (!token) {
      return;
    }
    setLoading(true);
    setStatusMessage(null);
    try {
      const response = await apiGet<OrganizationDetailResponse>("/organizations/me", { token });
      setDetail(response);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setDetail(null);
      } else {
        setStatusMessage(err instanceof Error ? err.message : "Unable to load organization");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadOrganization();
    }
  }, [token]);

  if (!isAdmin) {
    return <EmptyState title="Admin access required" description="Only platform admins can manage organization accounts right now." />;
  }

  if (loading) {
    return <LoadingState message="Loading organization..." />;
  }

  if (!detail) {
    return (
      <div className="space-y-6">
        <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
          <h1 className="text-2xl font-semibold text-slate-900">Organization setup</h1>
          <p className="mt-2 text-sm text-slate-600">
            Create the first org to prepare Buddybug for multi-user internal workflows and future team collaboration.
          </p>
        </section>

        <form
          className="space-y-4 rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm"
          onSubmit={(event) => {
            event.preventDefault();
            if (!token) {
              return;
            }
            setCreating(true);
            setStatusMessage(null);
            void apiPost<OrganizationRead>(
              "/organizations",
              {
                name: orgName,
                slug: orgSlug,
                is_active: true,
              },
              { token },
            )
              .then(() => loadOrganization())
              .catch((err) => setStatusMessage(err instanceof Error ? err.message : "Unable to create organization"))
              .finally(() => setCreating(false));
          }}
        >
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Organization name</span>
            <input
              value={orgName}
              onChange={(event) => setOrgName(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
              placeholder="Buddybug Team"
              required
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Slug</span>
            <input
              value={orgSlug}
              onChange={(event) => setOrgSlug(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
              placeholder="buddybug-team"
              required
            />
          </label>
          <button
            type="submit"
            disabled={creating}
            className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {creating ? "Creating..." : "Create organization"}
          </button>
        </form>

        {statusMessage ? (
          <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{statusMessage}</div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <OrganizationCard organization={detail.organization} />
      <InviteMemberForm
        submitting={adding}
        onSubmit={async (value: InviteMemberFormValue) => {
          if (!token) {
            return;
          }
          setAdding(true);
          setStatusMessage(null);
          try {
            await apiPost(
              `/organizations/${detail.organization.id}/members`,
              { user_id: value.user_id, role: value.role, is_active: true },
              { token },
            );
            await loadOrganization();
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to add member");
          } finally {
            setAdding(false);
          }
        }}
      />
      {statusMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{statusMessage}</div>
      ) : null}
      <OrganizationMembersTable
        memberships={detail.memberships}
        updatingId={updatingId}
        removingId={removingId}
        onRoleChange={async (membership: OrganizationMembershipRead, role: string) => {
          if (!token) {
            return;
          }
          setUpdatingId(membership.id);
          setStatusMessage(null);
          try {
            await apiPatch(`/organizations/members/${membership.id}`, { role }, { token });
            await loadOrganization();
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to update member role");
          } finally {
            setUpdatingId(null);
          }
        }}
        onRemove={async (membership: OrganizationMembershipRead) => {
          if (!token) {
            return;
          }
          setRemovingId(membership.id);
          setStatusMessage(null);
          try {
            await apiDelete(`/organizations/members/${membership.id}`, { token });
            await loadOrganization();
          } catch (err) {
            setStatusMessage(err instanceof Error ? err.message : "Unable to remove member");
          } finally {
            setRemovingId(null);
          }
        }}
      />
      <ActivityFeed token={token} entityType="organization" entityId={detail.organization.id} />
    </div>
  );
}
