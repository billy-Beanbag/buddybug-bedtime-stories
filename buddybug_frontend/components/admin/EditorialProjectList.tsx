"use client";

import Link from "next/link";
import { useState } from "react";

import type { EditorialProjectRead } from "@/lib/types";

export function EditorialProjectList({
  projects,
  onCreate,
}: {
  projects: EditorialProjectRead[];
  onCreate: (payload: {
    title: string;
    slug: string;
    age_band: string;
    language: string;
    source_type: string;
  }) => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [ageBand, setAgeBand] = useState("3-7");
  const [language, setLanguage] = useState("en");
  const [sourceType, setSourceType] = useState("manual");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onCreate({ title, slug, age_band: ageBand, language, source_type: sourceType });
      setTitle("");
      setSlug("");
      setAgeBand("3-7");
      setLanguage("en");
      setSourceType("manual");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="grid gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">New project</h3>
          <p className="mt-1 text-sm text-slate-600">Start a manual or hybrid editorial workflow.</p>
        </div>
        <input
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Project title"
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          required
        />
        <input
          value={slug}
          onChange={(event) => setSlug(event.target.value)}
          placeholder="project-slug"
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          required
        />
        <div className="grid gap-3 sm:grid-cols-3">
          <select
            value={ageBand}
            onChange={(event) => setAgeBand(event.target.value)}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            <option value="3-7">3-7</option>
            <option value="8-12">8-12</option>
          </select>
          <input
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
            placeholder="en"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
          <select
            value={sourceType}
            onChange={(event) => setSourceType(event.target.value)}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            <option value="manual">manual</option>
            <option value="mixed">mixed</option>
            <option value="ai_generated">ai_generated</option>
            <option value="classic_adaptation">classic_adaptation</option>
            <option value="curated_premise">curated_premise</option>
            <option value="llm_generated_idea">llm_generated_idea</option>
            <option value="parent_suggestion">parent_suggestion</option>
          </select>
        </div>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button
          type="submit"
          disabled={saving}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {saving ? "Creating..." : "Create project"}
        </button>
      </form>

      <div className="grid gap-3">
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/admin/editorial/${project.id}`}
            className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-900">{project.title}</h3>
                <p className="mt-1 text-sm text-slate-600">{project.slug}</p>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                {project.status}
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {project.age_band} • {project.language.toUpperCase()} • {project.source_type}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
