"use client";

import { useState } from "react";

export function IncidentUpdateForm({
  submitting,
  onSubmit,
}: {
  submitting?: boolean;
  onSubmit: (payload: { update_type: string; body: string }) => Promise<void>;
}) {
  const [updateType, setUpdateType] = useState("status_update");
  const [body, setBody] = useState("");

  return (
    <form
      className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={async (event) => {
        event.preventDefault();
        try {
          await onSubmit({ update_type: updateType, body });
          setBody("");
          setUpdateType("status_update");
        } catch {
          // Parent component surfaces request errors inline.
        }
      }}
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Add timeline update</h3>
        <p className="mt-1 text-sm text-slate-600">Capture mitigation notes, status changes, resolution details, or postmortem breadcrumbs.</p>
      </div>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Update type</span>
        <select
          value={updateType}
          onChange={(event) => setUpdateType(event.target.value)}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          disabled={submitting}
        >
          <option value="status_update">status_update</option>
          <option value="mitigation_note">mitigation_note</option>
          <option value="resolution_note">resolution_note</option>
          <option value="postmortem_note">postmortem_note</option>
        </select>
      </label>

      <label className="space-y-1 text-sm text-slate-700">
        <span>Update body</span>
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          rows={5}
          className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900"
          placeholder="What changed, what was mitigated, and what should the next admin know?"
          disabled={submitting}
        />
      </label>

      <button
        type="submit"
        disabled={submitting || !body.trim()}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Saving..." : "Add update"}
      </button>
    </form>
  );
}
