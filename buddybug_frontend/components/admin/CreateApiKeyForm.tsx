"use client";

import { useState } from "react";

export interface CreateApiKeyFormValue {
  name: string;
  scopes: string;
}

export function CreateApiKeyForm({
  submitting,
  onSubmit,
}: {
  submitting: boolean;
  onSubmit: (value: CreateApiKeyFormValue) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState("reporting.read");

  return (
    <form
      className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        void onSubmit({ name, scopes }).then(() => {
          setName("");
          setScopes("reporting.read");
        });
      }}
    >
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Create API key</h2>
        <p className="mt-1 text-sm text-slate-600">
          Use comma-separated scopes like `reporting.read`, `books.read`, or `campaigns.read` to keep access minimal.
        </p>
      </div>
      <div className="mt-4 grid gap-4">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Name</span>
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="Nightly reporting sync"
            required
          />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Scopes</span>
          <input
            value={scopes}
            onChange={(event) => setScopes(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="reporting.read, books.read"
            required
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={submitting || !name.trim() || !scopes.trim()}
        className="mt-4 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {submitting ? "Creating..." : "Create key"}
      </button>
    </form>
  );
}
