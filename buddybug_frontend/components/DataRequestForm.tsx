"use client";

import { useState } from "react";

import type { ChildProfileRead } from "@/lib/types";

interface DataRequestFormProps {
  childProfiles: ChildProfileRead[];
  submitting?: boolean;
  onSubmit: (value: {
    request_type: string;
    child_profile_id: number | null;
    reason: string;
  }) => Promise<void>;
}

const REQUEST_OPTIONS = [
  { value: "export_account_data", label: "Export account data" },
  { value: "export_child_data", label: "Export one child profile" },
  { value: "delete_account_data", label: "Request account deletion" },
  { value: "delete_child_data", label: "Request child data deletion" },
];

export function DataRequestForm({ childProfiles, submitting = false, onSubmit }: DataRequestFormProps) {
  const [requestType, setRequestType] = useState("export_account_data");
  const [childProfileId, setChildProfileId] = useState<string>("");
  const [reason, setReason] = useState("");

  const requiresChildProfile = requestType === "export_child_data" || requestType === "delete_child_data";

  return (
    <form
      className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit({
          request_type: requestType,
          child_profile_id: requiresChildProfile && childProfileId ? Number(childProfileId) : null,
          reason,
        }).then(() => {
          setReason("");
          if (!requiresChildProfile) {
            setChildProfileId("");
          }
        });
      }}
    >
      <div>
        <h2 className="text-2xl font-semibold text-slate-900">Request export or deletion</h2>
        <p className="mt-1 text-sm text-slate-600">
          Buddybug records export and deletion requests for internal follow-up. No destructive deletion happens automatically in this stage.
        </p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Request type</span>
        <select
          value={requestType}
          onChange={(event) => {
            setRequestType(event.target.value);
            if (!(event.target.value === "export_child_data" || event.target.value === "delete_child_data")) {
              setChildProfileId("");
            }
          }}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          disabled={submitting}
        >
          {REQUEST_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      {requiresChildProfile ? (
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Child profile</span>
          <select
            value={childProfileId}
            onChange={(event) => setChildProfileId(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            disabled={submitting}
            required
          >
            <option value="">Select a child profile</option>
            {childProfiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.display_name} ({profile.age_band})
              </option>
            ))}
          </select>
        </label>
      ) : null}

      <label className="block">
        <span className="mb-2 block text-sm font-medium text-slate-700">Reason</span>
        <textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          rows={3}
          placeholder="Optional context for your request"
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          disabled={submitting}
        />
      </label>

      <button
        type="submit"
        disabled={submitting || (requiresChildProfile && !childProfileId)}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Submitting request..." : "Submit request"}
      </button>
    </form>
  );
}
