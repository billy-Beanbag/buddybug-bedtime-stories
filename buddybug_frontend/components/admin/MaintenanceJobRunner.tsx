"use client";

import { useEffect, useState } from "react";

import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";

const JOB_OPTIONS = [
  {
    value: "rebuild_discovery_metadata",
    label: "rebuild_discovery_metadata",
    defaultKey: "rebuild-discovery-metadata",
    defaultTitle: "Rebuild discovery metadata",
    scopeHint: "all or book:{id}",
  },
  {
    value: "rebuild_account_health",
    label: "rebuild_account_health",
    defaultKey: "rebuild-account-health",
    defaultTitle: "Rebuild account health snapshots",
    scopeHint: "all or user:{id}",
  },
  {
    value: "rebuild_reengagement",
    label: "rebuild_reengagement",
    defaultKey: "rebuild-reengagement",
    defaultTitle: "Rebuild reengagement state",
    scopeHint: "all or user:{id}",
  },
  {
    value: "backfill_content_lane_keys",
    label: "backfill_content_lane_keys",
    defaultKey: "backfill-content-lane-keys",
    defaultTitle: "Backfill content lane keys",
    scopeHint: "all",
  },
  {
    value: "repair_download_packages",
    label: "repair_download_packages",
    defaultKey: "repair-download-packages",
    defaultTitle: "Repair missing download packages",
    scopeHint: "all or book:{id}",
  },
] as const;

export interface MaintenanceJobFormValue {
  key: string;
  title: string;
  description: string | null;
  job_type: string;
  target_scope: string | null;
  parameters_json: string | null;
}

export function MaintenanceJobRunner({
  creating,
  onCreate,
}: {
  creating?: boolean;
  onCreate: (payload: MaintenanceJobFormValue) => Promise<void>;
}) {
  const [jobType, setJobType] = useState<string>("rebuild_discovery_metadata");
  const [key, setKey] = useState<string>(JOB_OPTIONS[0].defaultKey);
  const [title, setTitle] = useState<string>(JOB_OPTIONS[0].defaultTitle);
  const [description, setDescription] = useState("");
  const [targetScope, setTargetScope] = useState("all");
  const [parametersJson, setParametersJson] = useState("");

  const selectedOption = JOB_OPTIONS.find((item) => item.value === jobType) || JOB_OPTIONS[0];

  useEffect(() => {
    setKey(selectedOption.defaultKey);
    setTitle(selectedOption.defaultTitle);
    setTargetScope("all");
    setParametersJson("");
  }, [selectedOption]);

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onCreate({
          key,
          title,
          description: description.trim() ? description : null,
          job_type: jobType,
          target_scope: targetScope.trim() ? targetScope : null,
          parameters_json: parametersJson.trim() ? parametersJson : null,
        })
          .then(() => {
            setDescription("");
            setParametersJson("");
          })
          .catch(() => {
            // Parent component surfaces request errors.
          });
      }}
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Create maintenance job</h3>
        <p className="mt-1 text-sm text-slate-600">Create a bounded admin-only backfill or rebuild job, then run it when you are ready.</p>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Job type</span>
        <select
          value={jobType}
          onChange={(event) => setJobType(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={creating}
        >
          {JOB_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm text-slate-700">
          <span>Key</span>
          <input
            value={key}
            onChange={(event) => setKey(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            disabled={creating}
          />
        </label>
        <label className="space-y-1 text-sm text-slate-700">
          <span>Scope</span>
          <input
            value={targetScope}
            onChange={(event) => setTargetScope(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
            placeholder={selectedOption.scopeHint}
            disabled={creating}
          />
        </label>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Title</span>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={creating}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Description</span>
        <textarea
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={3}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          placeholder="Optional operator-facing note about what this run is for"
          disabled={creating}
        />
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Parameters JSON</span>
        <textarea
          value={parametersJson}
          onChange={(event) => setParametersJson(event.target.value)}
          rows={4}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 font-mono text-sm text-slate-900"
          placeholder='Optional JSON, for example {"notes":"scoped dry run"}'
          disabled={creating}
        />
      </label>

      <button
        type="submit"
        disabled={creating || !key.trim() || !title.trim()}
        className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
      >
        {creating ? "Creating..." : "Create job"}
      </button>
    </form>
  );
}
