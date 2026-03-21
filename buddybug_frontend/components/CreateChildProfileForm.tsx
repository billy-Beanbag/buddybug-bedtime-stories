"use client";

import { useState } from "react";

import { apiPost } from "@/lib/api";
import type { ChildProfileSelectionResponse } from "@/lib/types";

interface CreateChildProfileFormProps {
  token: string;
  onCreated: () => Promise<void> | void;
}

export function CreateChildProfileForm({ token, onCreated }: CreateChildProfileFormProps) {
  const [displayName, setDisplayName] = useState("");
  const [ageBand, setAgeBand] = useState<"3-7" | "8-12">("3-7");
  const [language, setLanguage] = useState("en");
  const [birthYear, setBirthYear] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!displayName.trim()) {
      setError("Display name is required.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await apiPost<ChildProfileSelectionResponse>(
        "/child-profiles",
        {
          display_name: displayName.trim(),
          age_band: ageBand,
          language,
          birth_year: birthYear ? Number(birthYear) : null,
        },
        { token },
      );
      setDisplayName("");
      setBirthYear("");
      setAgeBand("3-7");
      setLanguage("en");
      await onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create child profile");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="relative space-y-4 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-5 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
      <div className="relative">
        <h2 className="text-xl font-semibold text-white">Create child profile</h2>
        <p className="mt-1 text-sm text-indigo-100">
          Add a simple reading profile for each child in the family account.
        </p>
      </div>
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-indigo-100">Display name</span>
        <input
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none placeholder:text-indigo-200/70"
          placeholder="Mia"
        />
      </label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-indigo-100">Age band</span>
          <select
            value={ageBand}
            onChange={(event) => setAgeBand(event.target.value as "3-7" | "8-12")}
            className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="3-7">3-7</option>
            <option value="8-12">8-12</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-indigo-100">Language</span>
          <select
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
            className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
          </select>
        </label>
      </div>
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-indigo-100">Birth year</span>
        <input
          value={birthYear}
          onChange={(event) => setBirthYear(event.target.value)}
          inputMode="numeric"
          className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm text-white outline-none placeholder:text-indigo-200/70"
          placeholder="2019"
        />
      </label>
      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-2xl border border-white/15 bg-white/10 px-4 py-3 font-medium text-white backdrop-blur disabled:opacity-60"
      >
        {submitting ? "Creating..." : "Create child profile"}
      </button>
    </form>
  );
}
