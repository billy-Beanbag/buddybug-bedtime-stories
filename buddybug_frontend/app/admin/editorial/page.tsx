"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { EditorialProjectList } from "@/components/admin/EditorialProjectList";
import { useAuth } from "@/context/AuthContext";
import { useFeatureFlags } from "@/context/FeatureFlagsContext";
import { apiGet, apiPost } from "@/lib/api";
import type { EditorialProjectRead } from "@/lib/types";

export default function AdminEditorialPage() {
  const { token, isEditor } = useAuth();
  const { isEnabled } = useFeatureFlags();
  const [projects, setProjects] = useState<EditorialProjectRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [language, setLanguage] = useState("");
  const [sourceType, setSourceType] = useState("");

  async function loadProjects() {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<EditorialProjectRead[]>("/editorial/projects", {
        token,
        query: {
          status: status || undefined,
          language: language || undefined,
          source_type: sourceType || undefined,
        },
      });
      setProjects(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load editorial projects");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProjects();
  }, [token, status, language, sourceType]);

  if (!isEnabled("editorial_tools_enabled")) {
    return <EmptyState title="Editorial tools are disabled" description="This internal workflow is currently hidden behind a feature flag." />;
  }

  if (!isEditor) {
    return <EmptyState title="Editorial access required" description="Only editor and admin users can open this area." />;
  }

  if (loading) {
    return <LoadingState message="Loading editorial projects..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load editorial projects" description={error} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Editorial projects</h2>
          <p className="mt-1 text-sm text-slate-600">Manage manual and hybrid publishing workflows.</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          <input
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
            placeholder="language"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          />
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="draft">draft</option>
            <option value="ready_for_preview">ready_for_preview</option>
            <option value="ready_for_publish">ready_for_publish</option>
            <option value="published">published</option>
            <option value="archived">archived</option>
          </select>
          <select
            value={sourceType}
            onChange={(event) => setSourceType(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All source types</option>
            <option value="manual">manual</option>
            <option value="mixed">mixed</option>
            <option value="ai_generated">ai_generated</option>
            <option value="curated_premise">curated_premise</option>
            <option value="llm_generated_idea">llm_generated_idea</option>
            <option value="parent_suggestion">parent_suggestion</option>
          </select>
        </div>
      </div>

      <EditorialProjectList
        projects={projects}
        onCreate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPost<EditorialProjectRead>("/editorial/projects", payload, { token });
          await loadProjects();
        }}
      />
    </div>
  );
}
