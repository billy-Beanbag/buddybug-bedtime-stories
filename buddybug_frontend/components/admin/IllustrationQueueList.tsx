"use client";

import Link from "next/link";
import { useState } from "react";

import { apiPost, resolveApiUrl } from "@/lib/api";
import type {
  AdminIllustrationSummary,
  IllustrationGenerateResponse,
  VisualReferenceAssetRead,
} from "@/lib/types";

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

export function IllustrationQueueList({
  illustrations,
  referencesByPage,
  token,
  onUpdated,
}: {
  illustrations: AdminIllustrationSummary[];
  referencesByPage: Record<number, VisualReferenceAssetRead[]>;
  token: string | null;
  onUpdated: () => Promise<void> | void;
}) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [expandedRejectId, setExpandedRejectId] = useState<number | null>(null);
  const [feedbackById, setFeedbackById] = useState<Record<number, string>>({});
  const [selectedTagsById, setSelectedTagsById] = useState<Record<number, string[]>>({});

  function getReaderHref(illustration: AdminIllustrationSummary) {
    if (!illustration.book_id) {
      return null;
    }

    return illustration.published || illustration.publication_status === "published"
      ? `/reader/${illustration.book_id}`
      : `/reader/${illustration.book_id}?preview=1`;
  }

  function buildFeedback(illustrationId: number) {
    const tags = selectedTagsById[illustrationId] ?? [];
    const notes = (feedbackById[illustrationId] || "").trim();
    return [...tags, notes].filter(Boolean).join(". ");
  }

  function toggleReasonTag(illustrationId: number, tag: string) {
    setSelectedTagsById((current) => {
      const existing = current[illustrationId] ?? [];
      const next = existing.includes(tag) ? existing.filter((item) => item !== tag) : [...existing, tag];
      return { ...current, [illustrationId]: next };
    });
  }

  async function handleApprove(illustrationId: number) {
    if (!token) {
      return;
    }

    setBusyId(illustrationId);
    setBusyAction("approve");
    setMessage(null);
    setError(null);
    try {
      await apiPost(`/illustrations/${illustrationId}/approve`, undefined, { token });
      setMessage("Illustration approved.");
      await onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to approve illustration");
    } finally {
      setBusyId(null);
      setBusyAction(null);
    }
  }

  async function handleReject(illustration: AdminIllustrationSummary, regenerate: boolean) {
    if (!token) {
      return;
    }

    const feedback = buildFeedback(illustration.id);
    if (!feedback) {
      setError("Add a rejection reason before rejecting an illustration.");
      setExpandedRejectId(illustration.id);
      return;
    }

    setBusyId(illustration.id);
    setBusyAction(regenerate ? "reject-regenerate" : "reject");
    setMessage(null);
    setError(null);
    try {
      setMessage("Rejecting the current illustration and saving your feedback...");
      await apiPost(`/illustrations/${illustration.id}/reject`, { generation_notes: feedback }, { token });
      if (regenerate) {
        setMessage("Feedback saved. Requesting a replacement illustration now...");
        await apiPost<IllustrationGenerateResponse>(
          "/illustrations/generate",
          {
            story_page_id: illustration.story_page_id,
            provider: illustration.provider === "manual_upload" ? undefined : illustration.provider,
            generation_notes: feedback,
          },
          { token },
        );
      }
      setMessage(
        regenerate
          ? "Illustration rejected. A replacement has been requested and the queue is refreshing."
          : "Illustration rejected.",
      );
      setExpandedRejectId(null);
      setMessage((current) => current ?? "Refreshing the illustration queue...");
      await onUpdated();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : regenerate
            ? "Unable to reject and regenerate illustration"
            : "Unable to reject illustration",
      );
    } finally {
      setBusyId(null);
      setBusyAction(null);
    }
  }

  if (!illustrations.length) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 p-6 text-sm text-slate-600">
        No illustrations are waiting in this queue.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      {illustrations.map((illustration) => (
        <div key={illustration.id} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-2">
              <p className="text-sm font-semibold text-slate-900">Illustration #{illustration.id}</p>
              <p className="text-sm font-medium text-slate-800">
                {illustration.story_draft_title || "Unknown story"}
              </p>
              <p className="text-sm text-slate-600">
                Draft {illustration.story_draft_id ?? "?"} • Page {illustration.page_number ?? illustration.story_page_id}
              </p>
              {illustration.scene_summary ? (
                <p className="max-w-2xl text-sm text-slate-600">{illustration.scene_summary}</p>
              ) : null}
              <p className="text-sm text-slate-600">Status: {illustration.approval_status}</p>
              <p className="text-sm text-slate-600">
                Version: {illustration.version_number} • Provider: {illustration.provider}
              </p>
              {(referencesByPage[illustration.story_page_id] ?? []).length ? (
                <div className="rounded-2xl bg-amber-50 px-3 py-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Reference assets in play</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(referencesByPage[illustration.story_page_id] ?? []).map((asset) => (
                      <a
                        key={asset.id}
                        href={resolveApiUrl(asset.image_url)}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-full border border-amber-200 bg-white px-3 py-1 text-xs font-medium text-amber-900"
                      >
                        {asset.reference_type}: {asset.name}
                      </a>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              {illustration.image_url ? (
                <a
                  href={resolveApiUrl(illustration.image_url)}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-2xl bg-sky-50 px-4 py-2 text-sm font-medium text-sky-800"
                >
                  Open image
                </a>
              ) : null}
              {getReaderHref(illustration) ? (
                <Link
                  href={getReaderHref(illustration) ?? "#"}
                  className="rounded-2xl bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-800"
                >
                  Open contextual preview
                </Link>
              ) : null}
              <button
                type="button"
                disabled={busyId === illustration.id}
                onClick={() => handleApprove(illustration.id)}
                className="rounded-2xl bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 disabled:opacity-60"
              >
                {busyId === illustration.id && busyAction === "approve" ? "Approving..." : "Approve"}
              </button>
              <button
                type="button"
                disabled={busyId === illustration.id}
                onClick={() =>
                  setExpandedRejectId((current) => (current === illustration.id ? null : illustration.id))
                }
                className="rounded-2xl bg-rose-50 px-4 py-2 text-sm font-medium text-rose-800 disabled:opacity-60"
              >
                Reject...
              </button>
            </div>
          </div>
          {expandedRejectId === illustration.id ? (
            <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50/70 p-4">
              <p className="text-sm font-semibold text-rose-900">Why are you rejecting this image?</p>
              <p className="mt-1 text-sm text-rose-800">
                The feedback below is saved and reused if you regenerate a new version.
              </p>
              {busyId === illustration.id ? (
                <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-900">
                  {busyAction === "reject-regenerate"
                    ? "Working: rejecting this version, then requesting a replacement illustration."
                    : busyAction === "reject"
                      ? "Working: rejecting this illustration and saving your feedback."
                      : "Working on this illustration..."}
                </div>
              ) : null}
              <div className="mt-3 flex flex-wrap gap-2">
                {REJECTION_REASON_OPTIONS.map((tag) => {
                  const isSelected = (selectedTagsById[illustration.id] ?? []).includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleReasonTag(illustration.id, tag)}
                      className={`rounded-full px-3 py-1 text-xs font-medium ${
                        isSelected
                          ? "bg-rose-600 text-white"
                          : "border border-rose-200 bg-white text-rose-800"
                      }`}
                    >
                      {tag}
                    </button>
                  );
                })}
              </div>
              <textarea
                value={feedbackById[illustration.id] ?? ""}
                onChange={(event) =>
                  setFeedbackById((current) => ({
                    ...current,
                    [illustration.id]: event.target.value,
                  }))
                }
                rows={4}
                placeholder="Add reviewer feedback, for example: Dolly should be tucked into her blanket and there should be no dogs in the room."
                className="mt-3 w-full rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none ring-0 placeholder:text-slate-400 focus:border-rose-400"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busyId === illustration.id}
                  onClick={() => handleReject(illustration, false)}
                  className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
                >
                  {busyId === illustration.id && busyAction === "reject" ? "Rejecting..." : "Reject only"}
                </button>
                <button
                  type="button"
                  disabled={busyId === illustration.id}
                  onClick={() => handleReject(illustration, true)}
                  className="rounded-2xl bg-amber-100 px-4 py-2 text-sm font-medium text-amber-900 disabled:opacity-60"
                >
                  {busyId === illustration.id && busyAction === "reject-regenerate"
                    ? "Rejecting and regenerating..."
                    : "Reject and regenerate"}
                </button>
                <button
                  type="button"
                  disabled={busyId === illustration.id}
                  onClick={() => setExpandedRejectId(null)}
                  className="rounded-2xl bg-white px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-60"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : null}
          {("image_url" in illustration && typeof illustration.image_url === "string" && illustration.image_url) ? (
            <div className="mt-4 overflow-hidden rounded-2xl bg-slate-100">
              <img
                src={resolveApiUrl(illustration.image_url)}
                alt={`Illustration ${illustration.id}`}
                className="h-48 w-full object-cover"
              />
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
