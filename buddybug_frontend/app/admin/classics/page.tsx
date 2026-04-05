"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import type { ClassicSourceRead } from "@/lib/types";

type ImportFormState = {
  title: string;
  source_text: string;
  source_url: string;
  source_author: string;
  source_origin_notes: string;
  public_domain_verified: boolean;
};

const INITIAL_FORM: ImportFormState = {
  title: "",
  source_text: "",
  source_url: "",
  source_author: "",
  source_origin_notes: "",
  public_domain_verified: false,
};

export default function AdminClassicsPage() {
  const { token } = useAuth();
  const [sources, setSources] = useState<ClassicSourceRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<ImportFormState>(INITIAL_FORM);

  async function loadSources() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<ClassicSourceRead[]>("/classics/sources", { token, query: { limit: 200 } });
      setSources(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load classics");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSources();
  }, [token]);

  async function handleImport(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await apiPost<ClassicSourceRead>(
        "/classics/sources",
        {
          ...form,
          source_author: form.source_author || null,
          source_origin_notes: form.source_origin_notes || null,
        },
        { token, timeoutMs: 90_000 },
      );
      setForm(INITIAL_FORM);
      await loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to import classic");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <LoadingState message="Loading classics workflow..." />;
  }

  if (error && sources.length === 0) {
    return <EmptyState title="Unable to load classics" description={error} />;
  }

  return (
    <div className="space-y-5">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="max-w-3xl">
          <h2 className="text-2xl font-semibold text-slate-900">Buddybug Classics</h2>
          <p className="mt-2 text-sm text-slate-600">
            Import a public-domain classic, adapt it with restrained Buddybug cameo magic, generate illustrations, review it
            internally, and publish it only when it is ready.
          </p>
        </div>
      </section>

      <form onSubmit={handleImport} className="grid gap-3 rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Import classic source</h3>
          <p className="mt-1 text-sm text-slate-600">
            Paste the original public-domain story text and keep the reference URL for later audit.
          </p>
        </div>
        <input
          value={form.title}
          onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
          placeholder="Goldilocks and the Three Bears"
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          required
        />
        <input
          value={form.source_url}
          onChange={(event) => setForm((current) => ({ ...current, source_url: event.target.value }))}
          placeholder="https://example.org/public-domain-source"
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          required
        />
        <div className="grid gap-3 md:grid-cols-2">
          <input
            value={form.source_author}
            onChange={(event) => setForm((current) => ({ ...current, source_author: event.target.value }))}
            placeholder="Source author"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
          <input
            value={form.source_origin_notes}
            onChange={(event) => setForm((current) => ({ ...current, source_origin_notes: event.target.value }))}
            placeholder="Origin notes"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        </div>
        <textarea
          value={form.source_text}
          onChange={(event) => setForm((current) => ({ ...current, source_text: event.target.value }))}
          rows={14}
          placeholder="Paste the original classic source text here"
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          required
        />
        <label className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <input
            type="checkbox"
            checked={form.public_domain_verified}
            onChange={(event) => setForm((current) => ({ ...current, public_domain_verified: event.target.checked }))}
          />
          <span>I confirm this source is genuinely public domain and safe to adapt internally.</span>
        </label>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <button
          type="submit"
          disabled={saving}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {saving ? "Importing..." : "Import classic"}
        </button>
      </form>

      <section className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-slate-900">Imported classics</h3>
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
            {sources.length} total
          </span>
        </div>
        {sources.length === 0 ? (
          <EmptyState
            title="No classics yet"
            description="Import one public-domain story to start the internal classics adaptation workflow."
          />
        ) : (
          <div className="grid gap-3">
            {sources.map((source) => (
              <Link
                key={source.id}
                href={`/admin/classics/${source.id}`}
                className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0">
                    <h4 className="text-lg font-semibold text-slate-900">{source.title}</h4>
                    <p className="mt-1 line-clamp-2 text-sm text-slate-600">{source.source_url}</p>
                    <p className="mt-2 text-xs text-slate-500">
                      {source.source_author || "Unknown author"} • {source.public_domain_verified ? "verified" : "verification needed"}
                    </p>
                  </div>
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700">
                    {source.import_status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
