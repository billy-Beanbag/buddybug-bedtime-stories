"use client";

import { useEffect, useState } from "react";

import { ActivityFeed } from "@/components/admin/ActivityFeed";
import { apiGet, apiPatch, apiPost, ApiError } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { EditorialStoryPageRead, StoryDraftReviewRead } from "@/lib/types";
import { DraftVersionHistory } from "@/components/admin/DraftVersionHistory";

export function DraftReviewEditor({
  draftId,
  token,
}: {
  draftId: number;
  token: string | null;
}) {
  const [draft, setDraft] = useState<StoryDraftReviewRead | null>(null);
  const [fullText, setFullText] = useState("");
  const [approvedText, setApprovedText] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [contentLaneKey, setContentLaneKey] = useState<string>("bedtime_3_7");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadDraft() {
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<StoryDraftReviewRead>(`/reviews/drafts/${draftId}`, { token });
      setDraft(response);
      setFullText(response.full_text);
      setApprovedText(response.approved_text || "");
      setReviewNotes(response.review_notes || "");
      setContentLaneKey(response.content_lane_key || "bedtime_3_7");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load draft");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDraft();
  }, [draftId, token]);

  async function saveDraftChanges({
    showMessage = true,
  }: {
    showMessage?: boolean;
  } = {}) {
    if (!token) {
      return null;
    }

    try {
      const updated = await apiPatch<StoryDraftReviewRead>(
        `/reviews/drafts/${draftId}`,
        {
          full_text: fullText,
          approved_text: approvedText || null,
          review_notes: reviewNotes || null,
          content_lane_key: contentLaneKey,
        },
        { token },
      );
      setDraft(updated);
      setFullText(updated.full_text);
      setApprovedText(updated.approved_text || "");
      setReviewNotes(updated.review_notes || "");
      if (showMessage) {
        setMessage("Draft edits saved.");
      }
      return updated;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save review changes");
      return null;
    }
  }

  async function handleSave() {
    if (!token) {
      return;
    }

    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await saveDraftChanges();
    } finally {
      setSaving(false);
    }
  }

  async function prepareApprovedDraftForPreview(updatedDraft: StoryDraftReviewRead) {
    if (!token) {
      return;
    }

    let pages = await apiGet<EditorialStoryPageRead[]>(`/story-pages/by-draft/${updatedDraft.id}`, { token });
    if (pages.length === 0) {
      setMessage("Draft approved. Generating the page plan...");
      await apiPost(
        "/story-pages/generate-plan",
        {
          story_draft_id: updatedDraft.id,
          target_page_count: undefined,
          min_pages: 8,
          max_pages: 14,
        },
        { token },
      );
      pages = await apiGet<EditorialStoryPageRead[]>(`/story-pages/by-draft/${updatedDraft.id}`, { token });
    }

    const pagesNeedingImages = pages.filter(
      (page) =>
        page.image_status === "prompt_ready" ||
        page.image_status === "image_rejected" ||
        page.image_status === "not_started" ||
        !page.image_url,
    );
    const failures: string[] = [];

    for (const [index, page] of pagesNeedingImages.entries()) {
      setMessage(`Draft approved. Generating illustration ${index + 1} of ${pagesNeedingImages.length}...`);
      try {
        await apiPost(
          "/illustrations/generate",
          {
            story_page_id: page.id,
          },
          { token },
        );
      } catch (err) {
        if (err instanceof ApiError) {
          failures.push(`Page ${page.page_number}: ${err.message}`);
        } else {
          failures.push(`Page ${page.page_number}: Unable to generate illustration`);
        }
      }
    }

    setMessage("Building the preview book...");
    await apiPost(`/editorial/story-drafts/${updatedDraft.id}/build-preview`, undefined, { token });

    if (failures.length > 0) {
      setMessage(
        `Draft approved. Preview book created, but ${failures.length} page image${failures.length === 1 ? "" : "s"} still need attention: ${failures.join(" | ")}`,
      );
      return;
    }

    setMessage("Draft approved. The page plan, illustrations, and preview book are ready for contextual review.");
  }

  async function handleStatusAction(
    action: "approve" | "needs-revision" | "reject" | "reset-to-review",
  ) {
    if (!token) {
      return;
    }

    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const savedDraft = await saveDraftChanges({ showMessage: false });
      if (!savedDraft) {
        return;
      }
      const payload =
        action === "needs-revision" || action === "reject" ? { review_notes: reviewNotes || null } : undefined;
      const updated = await apiPost<StoryDraftReviewRead>(`/reviews/drafts/${draftId}/${action}`, payload, {
        token,
      });
      setDraft(updated);
      setFullText(updated.full_text);
      setApprovedText(updated.approved_text || "");
      setReviewNotes(updated.review_notes || "");
      setContentLaneKey(updated.content_lane_key || "bedtime_3_7");
      if (action === "approve") {
        await prepareApprovedDraftForPreview(updated);
      } else {
        setMessage(`Draft ${action} completed.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Unable to run ${action}`);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading draft review...
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        Draft detail could not be loaded.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900">{draft.title}</h2>
            <p className="mt-2 text-sm text-slate-600">{draft.summary}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-2">
              <span className="text-sm font-medium text-slate-700">Type:</span>
              <select
                value={contentLaneKey}
                onChange={(e) => setContentLaneKey(e.target.value)}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900"
              >
                <option value="bedtime_3_7">Bedtime</option>
                <option value="story_adventures_8_12">Adventure</option>
              </select>
            </label>
            <span className="rounded-full bg-amber-50 px-3 py-2 text-sm font-medium text-amber-700">
              {draft.review_status}
            </span>
          </div>
        </div>
      </section>

      <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Review notes</span>
          <textarea
            value={reviewNotes}
            onChange={(event) => setReviewNotes(event.target.value)}
            rows={4}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Full text</span>
          <textarea
            value={fullText}
            onChange={(event) => setFullText(event.target.value)}
            rows={14}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm leading-6 text-slate-900 outline-none"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Approved text</span>
          <textarea
            value={approvedText}
            onChange={(event) => setApprovedText(event.target.value)}
            rows={10}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm leading-6 text-slate-900 outline-none"
          />
        </label>

        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={saving}
            onClick={handleSave}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Save draft edits
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => handleStatusAction("approve")}
            className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800 disabled:opacity-60"
          >
            Approve for illustration
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => handleStatusAction("needs-revision")}
            className="rounded-2xl bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800 disabled:opacity-60"
          >
            Mark needs revision
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => handleStatusAction("reject")}
            className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-800 disabled:opacity-60"
          >
            Reject draft
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => handleStatusAction("reset-to-review")}
            className="rounded-2xl bg-slate-100 px-4 py-3 text-sm font-medium text-slate-800 disabled:opacity-60"
          >
            Reset to review
          </button>
        </div>
      </section>

      <DraftVersionHistory
        draftId={draftId}
        token={token}
        onRolledBack={async () => {
          await loadDraft();
        }}
      />

      <ActivityFeed token={token} entityType="story_draft" entityId={draftId} />
    </div>
  );
}
