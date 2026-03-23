"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { AdminStoryIdeaSummary } from "@/lib/types";

export default function AdminIdeasPage() {
  const { token } = useAuth();
  const [ideas, setIdeas] = useState<AdminStoryIdeaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const BEDTIME_LANE = "bedtime_3_7";
  const ADVENTURE_LANE = "story_adventures_8_12";
  const [generateRoute, setGenerateRoute] = useState(BEDTIME_LANE);
  const [generating, setGenerating] = useState(false);

  async function handleGenerateIdeas() {
    if (!token) return;
    setGenerating(true);
    setMessage(null);
    setError(null);
    try {
      await apiPost(
        "/story-ideas/generate",
        {
          count: 5,
          // Must match ContentLane.age_band in the API. Both canonical lanes use 3–7 today; adventure is still
          // story_adventures_8_12 (lane key) with age_band 3–7 in seed until 8–12 is enabled server-side.
          age_band: "3-7",
          content_lane_key: generateRoute,
          bedtime_only: generateRoute === BEDTIME_LANE,
        },
        { token },
      );
      setMessage("Ideas generated. Refresh to see them.");
      await loadIdeas();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate ideas");
    } finally {
      setGenerating(false);
    }
  }

  async function loadIdeas() {
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<AdminStoryIdeaSummary[]>("/admin/ideas/queue", {
        token,
        query: { status: status || undefined },
      });
      setIdeas(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load ideas queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadIdeas();
  }, [token, status]);

  async function handleIdeaAction(
    ideaId: number,
    action: "select" | "reject",
    contentLaneKey?: string,
  ) {
    if (!token) return;
    setMessage(null);
    setError(null);
    try {
      const body = action === "select" && contentLaneKey ? { content_lane_key: contentLaneKey } : undefined;
      await apiPost(`/story-ideas/${ideaId}/${action}`, body, { token });
      setMessage(
        action === "reject"
          ? "Idea rejected."
          : contentLaneKey === BEDTIME_LANE
            ? "Idea selected as Bedtime."
            : contentLaneKey === ADVENTURE_LANE
              ? "Idea selected as Adventure."
              : "Idea selected.",
      );
      await loadIdeas();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Unable to ${action} idea`);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Ideas queue</h2>
          <p className="mt-1 text-sm text-slate-600">Review story ideas waiting to be selected or rejected.</p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-medium text-slate-500">Generate ideas (route)</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setGenerateRoute(BEDTIME_LANE)}
                className={`rounded-2xl px-4 py-2 text-sm font-medium ${
                  generateRoute === BEDTIME_LANE ? "bg-indigo-100 text-indigo-900" : "bg-slate-100 text-slate-600"
                }`}
              >
                Bedtime
              </button>
              <button
                type="button"
                onClick={() => setGenerateRoute(ADVENTURE_LANE)}
                className={`rounded-2xl px-4 py-2 text-sm font-medium ${
                  generateRoute === ADVENTURE_LANE ? "bg-amber-100 text-amber-900" : "bg-slate-100 text-slate-600"
                }`}
              >
                Adventure
              </button>
            </div>
          </div>
          <button
            type="button"
            disabled={generating}
            onClick={() => void handleGenerateIdeas()}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON} disabled:opacity-60`}
          >
            {generating ? "Generating…" : "Generate 5 ideas"}
          </button>
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="idea_pending">Idea pending</option>
            <option value="idea_selected">Idea selected</option>
            <option value="idea_rejected">Idea rejected</option>
          </select>
          <button
            type="button"
            onClick={() => void loadIdeas()}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Refresh
          </button>
        </div>
      </div>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {loading ? <LoadingState message="Loading ideas queue..." /> : null}

      {!loading && !ideas.length ? (
        <EmptyState
          title="No ideas found"
          description="Generate ideas using the Bedtime or Adventure route above, or switch the status filter to see selected/rejected ideas."
        />
      ) : null}

      {!loading ? (
        <div className="space-y-3">
          {ideas.map((idea) => (
            <div key={idea.id} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <h3 className="text-base font-semibold text-slate-900">{idea.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{idea.premise}</p>
                  <p className="mt-2 text-sm text-slate-500">
                    {idea.tone} • {idea.setting} • {idea.theme}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-700">{idea.status}</span>
                  {idea.status === "idea_pending" ? (
                    <>
                      <button
                        type="button"
                        onClick={() => handleIdeaAction(idea.id, "select", BEDTIME_LANE)}
                        className="rounded-2xl bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-800"
                        title="Select as Bedtime story (calm, gentle, 3–7)"
                      >
                        Select as Bedtime
                      </button>
                      <button
                        type="button"
                        onClick={() => handleIdeaAction(idea.id, "select", ADVENTURE_LANE)}
                        className="rounded-2xl bg-amber-50 px-4 py-2 text-sm font-medium text-amber-800"
                        title="Select as Adventure story (richer plots; same 3–7 age band as backend content lane)"
                      >
                        Select as Adventure
                      </button>
                      <button
                        type="button"
                        onClick={() => handleIdeaAction(idea.id, "reject")}
                        className="rounded-2xl bg-rose-50 px-4 py-2 text-sm font-medium text-rose-800"
                      >
                        Reject
                      </button>
                    </>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
