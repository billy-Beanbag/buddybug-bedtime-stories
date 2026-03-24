"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { apiGet, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON, ADMIN_SECONDARY_BUTTON } from "@/lib/admin-styles";
import type { AdminIllustrationSummary, EditorialStoryPageRead, ReaderPageRead } from "@/lib/types";

/** Fallback: resolve source_story_page_id from book+page when reader page lacks it */
async function fetchSourceStoryPageId(
  bookId: number,
  pageNumber: number,
  pageIndex: number | null,
  token: string | null,
): Promise<number | null> {
  if (!token) return null;
  const query = pageIndex != null ? { page_index: pageIndex } : undefined;
  try {
    const res = await apiGet<{ source_story_page_id: number | null }>(
      `/reader/books/${bookId}/pages/${pageNumber}/source-story-page`,
      { token, query },
    );
    return res.source_story_page_id ?? null;
  } catch {
    return null;
  }
}

async function fetchStoryDraftId(bookId: number, token: string | null): Promise<number | null> {
  if (!token) return null;
  try {
    const res = await apiGet<{ story_draft_id: number }>(`/reader/books/${bookId}/story-draft-id`, { token });
    return res.story_draft_id ?? null;
  } catch {
    return null;
  }
}

function NoLinkedStoryPageState({
  bookId,
  storyDraftId: initialStoryDraftId,
  token,
  onPreviewUpdated,
}: {
  bookId: number;
  storyDraftId: number | null;
  token: string | null;
  onPreviewUpdated: () => Promise<void> | void;
}) {
  const [storyDraftId, setStoryDraftId] = useState<number | null>(initialStoryDraftId);
  const [fetchingDraftId, setFetchingDraftId] = useState(!initialStoryDraftId && !!token && bookId > 0);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialStoryDraftId != null) {
      setStoryDraftId(initialStoryDraftId);
      setFetchingDraftId(false);
      return;
    }
    if (!token || !bookId) {
      setFetchingDraftId(false);
      return;
    }
    let cancelled = false;
    setFetchingDraftId(true);
    fetchStoryDraftId(bookId, token).then((id) => {
      if (!cancelled) {
        setStoryDraftId(id);
      }
    }).finally(() => {
      if (!cancelled) setFetchingDraftId(false);
    });
    return () => {
      cancelled = true;
    };
  }, [bookId, initialStoryDraftId, token]);

  async function handleRebuild() {
    if (!token || !storyDraftId) return;
    setRebuilding(true);
    setError(null);
    try {
      await apiPost(`/editorial/story-drafts/${storyDraftId}/build-preview`, undefined, { token, timeoutMs: 60_000 });
      await onPreviewUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rebuild preview");
    } finally {
      setRebuilding(false);
    }
  }

  return (
    <section className="rounded-[2rem] border border-amber-100 bg-amber-50/60 p-4 shadow-sm">
      <p className="text-sm text-amber-800">
        This page has no linked story page. Rebuild the preview to enable illustration review.
      </p>
      {storyDraftId && token ? (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={rebuilding}
            onClick={() => void handleRebuild()}
            className="rounded-2xl border border-amber-300 bg-amber-100 px-4 py-2 text-sm font-medium text-amber-900 disabled:opacity-60"
          >
            {rebuilding ? "Rebuilding..." : "Rebuild preview now"}
          </button>
          <Link
            href="/admin/workflow"
            className="rounded-2xl border border-amber-300 bg-white px-4 py-2 text-sm font-medium text-amber-900"
          >
            Open workflow
          </Link>
        </div>
      ) : (
        <Link
          href="/admin/workflow"
          className="mt-3 inline-flex rounded-2xl border border-amber-300 bg-amber-100 px-4 py-2 text-sm font-medium text-amber-900"
        >
          Open workflow
        </Link>
      )}
      {error ? <p className="mt-2 text-sm text-rose-600">{error}</p> : null}
    </section>
  );
}

const REJECTION_REASON_OPTIONS = [
  "Out of sync with the scene",
  "Missing key character",
  "No dogs",
  "Wrong pose or action",
  "Wrong setting",
  "Poor bedtime mood",
  "Character design drift",
  "Composition needs work",
];

export function PreviewIllustrationReviewPanel({
  page,
  pageIndex,
  bookId,
  storyDraftId,
  pageMapping,
  token,
  onPreviewUpdated,
}: {
  page: ReaderPageRead;
  pageIndex: number;
  bookId: number;
  storyDraftId: number | null;
  pageMapping: Record<number, number> | null | undefined;
  token: string | null;
  onPreviewUpdated: () => Promise<void> | void;
}) {
  const initialStoryPageId =
    page.source_story_page_id ?? pageMapping?.[page.page_number] ?? null;
  const needsFallback = initialStoryPageId == null && bookId > 0 && page.page_number > 0;
  const [resolvedStoryPageId, setResolvedStoryPageId] = useState<number | null>(initialStoryPageId);
  const [resolvingFallback, setResolvingFallback] = useState(needsFallback);
  const storyPageId = resolvedStoryPageId ?? initialStoryPageId;

  useEffect(() => {
    setResolvedStoryPageId(initialStoryPageId);
    const needs = initialStoryPageId == null && bookId > 0 && page.page_number > 0;
    setResolvingFallback(needs);
  }, [page.id, page.page_number, bookId, initialStoryPageId]);

  const resolveFallback = useCallback(async () => {
    if (initialStoryPageId != null || !bookId || page.page_number <= 0) return;
    setResolvingFallback(true);
    try {
      const id = await fetchSourceStoryPageId(bookId, page.page_number, pageIndex, token);
      setResolvedStoryPageId(id);
    } finally {
      setResolvingFallback(false);
    }
  }, [bookId, initialStoryPageId, page.page_number, pageIndex, token]);

  const [storyPage, setStoryPage] = useState<EditorialStoryPageRead | null>(null);
  const [illustrations, setIllustrations] = useState<AdminIllustrationSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [busyAction, setBusyAction] = useState<"approve" | "reject" | "reject-regenerate" | "generate" | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showRejectForm, setShowRejectForm] = useState(false);

  const latestIllustration = useMemo(() => illustrations[0] ?? null, [illustrations]);

  function buildFeedback() {
    return [...selectedTags, feedback.trim()].filter(Boolean).join(". ");
  }

  function toggleReasonTag(tag: string) {
    setSelectedTags((current) =>
      current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag],
    );
  }

  async function loadReviewState() {
    if (!token || !storyPageId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [pageResponse, illustrationsResponse] = await Promise.all([
        apiGet<EditorialStoryPageRead>(`/story-pages/${storyPageId}`, { token }),
        apiGet<AdminIllustrationSummary[]>(`/illustrations/by-page/${storyPageId}`, { token }),
      ]);
      setStoryPage(pageResponse);
      setIllustrations(illustrationsResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load preview review tools");
    } finally {
      setLoading(false);
    }
  }

  async function rebuildPreview() {
    if (!token || !storyPage) {
      return;
    }
    await apiPost(`/editorial/story-drafts/${storyPage.story_draft_id}/build-preview`, undefined, { token, timeoutMs: 60_000 });
    await Promise.all([loadReviewState(), onPreviewUpdated()]);
  }

  async function handleApprove() {
    if (!token || !latestIllustration) {
      return;
    }
    setBusyAction("approve");
    setMessage(null);
    setError(null);
    try {
      await apiPost(`/illustrations/${latestIllustration.id}/approve`, undefined, { token, timeoutMs: 60_000 });
      await rebuildPreview();
      setMessage("Illustration approved and preview refreshed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve illustration");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleReject(regenerate: boolean) {
    if (!token || !storyPageId) {
      return;
    }
    const combinedFeedback = buildFeedback();
    if (!combinedFeedback) {
      setError("Add a rejection reason before rejecting or regenerating.");
      setShowRejectForm(true);
      return;
    }

    setBusyAction(regenerate ? "reject-regenerate" : latestIllustration ? "reject" : "generate");
    setMessage(null);
    setError(null);
    try {
      if (regenerate || !latestIllustration) {
        await apiPost(
          "/illustrations/generate",
          {
            story_page_id: storyPageId,
            generation_notes: combinedFeedback,
          },
          { token, timeoutMs: 180_000 },
        );
      }
      if (latestIllustration) {
        await apiPost(
          `/illustrations/${latestIllustration.id}/reject`,
          { generation_notes: combinedFeedback },
          { token, timeoutMs: 60_000 },
        );
      }
      await rebuildPreview();
      setShowRejectForm(false);
      setMessage(
        regenerate || !latestIllustration
          ? "Replacement illustration requested and preview refreshed."
          : "Illustration rejected. Preview refreshed.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : regenerate || !latestIllustration
            ? "Unable to regenerate illustration"
            : "Unable to reject illustration",
      );
    } finally {
      setBusyAction(null);
    }
  }

  useEffect(() => {
    void resolveFallback();
  }, [resolveFallback]);

  useEffect(() => {
    setShowRejectForm(false);
    setMessage(null);
    setError(null);
    setFeedback("");
    setSelectedTags([]);
    setStoryPage(null);
    setIllustrations([]);
    void loadReviewState();
  }, [storyPageId, token]);

  if (resolvingFallback) {
    return (
      <section className="rounded-[2rem] border border-indigo-100 bg-indigo-50/60 p-4 shadow-sm">
        <p className="text-sm text-slate-600">Loading preview review tools…</p>
      </section>
    );
  }

  if (!storyPageId) {
    return (
      <NoLinkedStoryPageState
        bookId={bookId}
        storyDraftId={storyDraftId}
        token={token}
        onPreviewUpdated={onPreviewUpdated}
      />
    );
  }

  return (
    <section className="rounded-[2rem] border border-indigo-100 bg-indigo-50/60 p-4 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="inline-flex rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-indigo-700">
            Preview review
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Review this page image in story context</h3>
            <p className="mt-1 text-sm text-slate-600">
              Approve or correct the illustration while the text is visible beside it.
            </p>
          </div>
          <p className="text-sm text-slate-700">
            {loading
              ? "Loading review state..."
              : `Page status: ${storyPage?.image_status ?? "unknown"}${latestIllustration ? ` • Latest version ${latestIllustration.version_number} is ${latestIllustration.approval_status}` : " • No illustration version exists yet."}`}
          </p>
          {storyPage?.scene_summary ? <p className="text-sm text-slate-600">{storyPage.scene_summary}</p> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={!latestIllustration || busyAction !== null || latestIllustration.approval_status === "approved"}
            onClick={() => void handleApprove()}
            className={`rounded-2xl px-4 py-2 text-sm font-medium disabled:opacity-60 ${ADMIN_PRIMARY_BUTTON}`}
          >
            {busyAction === "approve" ? "Approving..." : latestIllustration?.approval_status === "approved" ? "Approved" : "Approve image"}
          </button>
          <button
            type="button"
            disabled={busyAction !== null}
            onClick={() => setShowRejectForm((current) => !current)}
            className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_SECONDARY_BUTTON} disabled:opacity-60`}
          >
            {latestIllustration ? "Reject..." : "Generate image"}
          </button>
        </div>
      </div>

      {message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}

      {showRejectForm ? (
        <div className="mt-4 rounded-3xl border border-rose-200 bg-white/80 p-4">
          <p className="text-sm font-semibold text-rose-900">
            {latestIllustration ? "What needs changing on this image?" : "What should this missing image show?"}
          </p>
          <p className="mt-1 text-sm text-rose-800">
            Your notes are added back into the prompt before a replacement is generated.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {REJECTION_REASON_OPTIONS.map((tag) => {
              const isSelected = selectedTags.includes(tag);
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleReasonTag(tag)}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    isSelected ? "bg-rose-600 text-white" : "border border-rose-200 bg-white text-rose-800"
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
          <textarea
            value={feedback}
            onChange={(event) => setFeedback(event.target.value)}
            rows={4}
            placeholder="For example: The dogs should be in the kitchen with Dolly, and the blanket should look bedtime-cozy."
            className="mt-3 w-full rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            {latestIllustration ? (
              <button
                type="button"
                disabled={busyAction !== null}
                onClick={() => void handleReject(false)}
                className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
              >
                {busyAction === "reject" ? "Rejecting..." : "Reject only"}
              </button>
            ) : null}
            <button
              type="button"
              disabled={busyAction !== null}
              onClick={() => void handleReject(true)}
              className="rounded-2xl bg-amber-100 px-4 py-2 text-sm font-medium text-amber-900 disabled:opacity-60"
            >
              {busyAction === "reject-regenerate" || busyAction === "generate"
                ? latestIllustration
                  ? "Rejecting and regenerating..."
                  : "Generating..."
                : latestIllustration
                  ? "Reject and regenerate"
                  : "Generate image"}
            </button>
            <button
              type="button"
              disabled={busyAction !== null}
              onClick={() => setShowRejectForm(false)}
              className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_SECONDARY_BUTTON} disabled:opacity-60`}
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
