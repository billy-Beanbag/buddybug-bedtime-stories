"use client";

import { useEffect, useState } from "react";

import type { FeatureFlagRead } from "@/lib/types";

export interface FeatureFlagFormValue {
  key: string;
  name: string;
  description: string;
  enabled: boolean;
  rollout_percentage: number;
  environments: string;
  target_subscription_tiers: string;
  target_languages: string;
  target_age_bands: string;
  target_roles: string;
  target_user_ids: string;
  target_countries: string;
  target_beta_cohorts: string;
  is_internal_only: boolean;
}

const EMPTY_FORM: FeatureFlagFormValue = {
  key: "",
  name: "",
  description: "",
  enabled: false,
  rollout_percentage: 100,
  environments: "",
  target_subscription_tiers: "",
  target_languages: "",
  target_age_bands: "",
  target_roles: "",
  target_user_ids: "",
  target_countries: "",
  target_beta_cohorts: "",
  is_internal_only: false,
};

function toFormValue(flag?: FeatureFlagRead | null): FeatureFlagFormValue {
  if (!flag) {
    return EMPTY_FORM;
  }
  return {
    key: flag.key,
    name: flag.name,
    description: flag.description || "",
    enabled: flag.enabled,
    rollout_percentage: flag.rollout_percentage,
    environments: flag.environments || "",
    target_subscription_tiers: flag.target_subscription_tiers || "",
    target_languages: flag.target_languages || "",
    target_age_bands: flag.target_age_bands || "",
    target_roles: flag.target_roles || "",
    target_user_ids: flag.target_user_ids || "",
    target_countries: flag.target_countries || "",
    target_beta_cohorts: flag.target_beta_cohorts || "",
    is_internal_only: flag.is_internal_only,
  };
}

interface FeatureFlagEditorProps {
  flag?: FeatureFlagRead | null;
  submitting?: boolean;
  onSubmit: (value: FeatureFlagFormValue) => Promise<void>;
  onCancel?: () => void;
}

export function FeatureFlagEditor({ flag, submitting = false, onSubmit, onCancel }: FeatureFlagEditorProps) {
  const [form, setForm] = useState<FeatureFlagFormValue>(() => toFormValue(flag));

  useEffect(() => {
    setForm(toFormValue(flag));
  }, [flag]);

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit(form);
      }}
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">{flag ? "Edit feature flag" : "Create feature flag"}</h3>
        <p className="mt-1 text-sm text-slate-600">Use simple targeting rules so release behavior stays easy to explain.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Key</span>
          <input
            value={form.key}
            onChange={(event) => setForm((current) => ({ ...current, key: event.target.value }))}
            placeholder="offline_downloads_enabled"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting || Boolean(flag)}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Name</span>
          <input
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            placeholder="Offline downloads"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Description</span>
        <textarea
          value={form.description}
          onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
          rows={3}
          placeholder="What this flag protects or stages."
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={submitting}
        />
      </label>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Rollout percentage</span>
          <input
            type="number"
            min={0}
            max={100}
            value={form.rollout_percentage}
            onChange={(event) =>
              setForm((current) => ({
                ...current,
                rollout_percentage: Number(event.target.value || 0),
              }))
            }
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.enabled}
            onChange={(event) => setForm((current) => ({ ...current, enabled: event.target.checked }))}
            disabled={submitting}
          />
          Enabled
        </label>
        <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.is_internal_only}
            onChange={(event) => setForm((current) => ({ ...current, is_internal_only: event.target.checked }))}
            disabled={submitting}
          />
          Internal only
        </label>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Environments</span>
          <input
            value={form.environments}
            onChange={(event) => setForm((current) => ({ ...current, environments: event.target.value }))}
            placeholder="development,staging,production"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Subscription tiers</span>
          <input
            value={form.target_subscription_tiers}
            onChange={(event) =>
              setForm((current) => ({ ...current, target_subscription_tiers: event.target.value }))
            }
            placeholder="premium"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Languages</span>
          <input
            value={form.target_languages}
            onChange={(event) => setForm((current) => ({ ...current, target_languages: event.target.value }))}
            placeholder="en,es"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Age bands</span>
          <input
            value={form.target_age_bands}
            onChange={(event) => setForm((current) => ({ ...current, target_age_bands: event.target.value }))}
            placeholder="3-7,8-12"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Roles</span>
          <input
            value={form.target_roles}
            onChange={(event) => setForm((current) => ({ ...current, target_roles: event.target.value }))}
            placeholder="admin,editor,authenticated,guest,premium"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Countries</span>
          <input
            value={form.target_countries}
            onChange={(event) => setForm((current) => ({ ...current, target_countries: event.target.value }))}
            placeholder="us,gb,ca"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Beta cohorts</span>
          <input
            value={form.target_beta_cohorts}
            onChange={(event) => setForm((current) => ({ ...current, target_beta_cohorts: event.target.value }))}
            placeholder="offline_sync_beta,educator_beta"
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={submitting}
          />
        </label>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Explicit user IDs</span>
        <input
          value={form.target_user_ids}
          onChange={(event) => setForm((current) => ({ ...current, target_user_ids: event.target.value }))}
          placeholder="12,34"
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={submitting}
        />
      </label>

      <div className="flex flex-wrap gap-3">
        <button
          type="submit"
          disabled={submitting}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Saving..." : flag ? "Save changes" : "Create flag"}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
          >
            Cancel
          </button>
        ) : null}
      </div>
    </form>
  );
}
