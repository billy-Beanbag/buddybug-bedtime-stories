"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { ApiError, apiGet, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON, ADMIN_SECONDARY_BUTTON } from "@/lib/admin-styles";
import type { AdminStoryPageSummary, IllustrationGenerateResponse, IllustrationPromptPackageRead } from "@/lib/types";

const PROVIDER_OPTIONS = [
  { value: "", label: "Configured default" },
  { value: "mock", label: "Mock storyboard" },
  { value: "openai", label: "Live AI image" },
];

function AdminStoryPagesPageContent() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const draftIdFilter = searchParams.get("draftId");
  const [pages, setPages] = useState<AdminStoryPageSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [imageStatus, setImageStatus] = useState("");
  const [provider, setProvider] = useState("");
  const [busyPageId, setBusyPageId] = useState<number | null>(null);
  const [previewingPageId, setPreviewingPageId] = useState<number | null>(null);
  const [preview, setPreview] = useState<IllustrationPromptPackageRead | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  function formatGenerationError(err: unknown) {
    if (err instanceof ApiError && err.message.includes("status 429")) {
      return "The live illustration provider is rate-limiting requests right now. Wait a moment and try again, or switch the provider to Mock storyboard if you want to keep moving.";
    }
    return err instanceof Error ? err.message : "Unable to generate illustration";
  }

  async function loadPages() {
    if (!token) {
      return;
    }

    setLoading(true);
    setLoadError(null);
    try {
      const response = await apiGet<AdminStoryPageSummary[]>("/admin/story-pages/queue", {
        token,
        query: { image_status: imageStatus || undefined },
      });
      setPages(response);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Unable to load story pages");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPages();
  }, [token, imageStatus]);

  async function handleGenerateIllustration(storyPageId: number) {
    if (!token) {
      return;
    }

    setMessage(null);
    setActionError(null);
    setBusyPageId(storyPageId);
    try {
      const response = await apiPost<IllustrationGenerateResponse>(
        "/illustrations/generate",
        { story_page_id: storyPageId, provider: provider || undefined },
        { token },
      );
      setMessage(`Illustration generated with ${response.illustration.provider}.`);
      if (preview?.story_page_id === storyPageId) {
        setPreview(null);
      }
      await loadPages();
    } catch (err) {
      setActionError(formatGenerationError(err));
    } finally {
      setBusyPageId(null);
    }
  }

  async function handlePreviewIllustration(storyPageId: number) {
    if (!token) {
      return;
    }

    if (preview?.story_page_id === storyPageId) {
      setPreview(null);
      setPreviewError(null);
      setPreviewingPageId(null);
      return;
    }

    setPreview(null);
    setPreviewError(null);
    setMessage(null);
    setActionError(null);
    setPreviewingPageId(storyPageId);
    try {
      const response = await apiPost<IllustrationPromptPackageRead>(
        "/illustrations/generate/preview",
        { story_page_id: storyPageId, provider: provider || undefined },
        { token },
      );
      setPreview(response);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : "Unable to preview illustration prompt");
    } finally {
      setPreviewingPageId(null);
    }
  }

  const groupedPages = useMemo(() => {
    const filteredPages = draftIdFilter
      ? pages.filter((page) => String(page.story_draft_id) === draftIdFilter)
      : pages;

    return filteredPages.reduce<Record<string, AdminStoryPageSummary[]>>((acc, page) => {
      const key = String(page.story_draft_id);
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(page);
      return acc;
    }, {});
  }, [draftIdFilter, pages]);

  if (loading) {
    return <LoadingState message="Loading story page queue..." />;
  }

  if (loadError) {
    return <EmptyState title="Unable to load story pages" description={loadError} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Page plan support</h2>
          <p className="mt-1 text-sm text-slate-600">
            Monitor planned pages and manually retry image generation only when the automatic post-approval step needs help.
          </p>
          {draftIdFilter ? (
            <p className="mt-2 text-sm text-indigo-700">
              Focused on draft {draftIdFilter}.{" "}
              <Link href="/admin/story-pages" className="font-medium underline-offset-4 hover:underline">
                Clear filter
              </Link>
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            value={imageStatus}
            onChange={(event) => setImageStatus(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="prompt_ready">Prompt ready</option>
            <option value="image_generated">Image generated</option>
            <option value="image_approved">Image approved</option>
            <option value="image_rejected">Image rejected</option>
          </select>
          <select
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            {PROVIDER_OPTIONS.map((option) => (
              <option key={option.value || "default"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void loadPages()}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="rounded-3xl border border-sky-100 bg-sky-50/70 p-4">
        <p className="text-sm font-semibold text-sky-900">Normal path</p>
        <p className="mt-1 text-sm text-sky-800">
          After a draft is approved, BuddyBug now tries to build the page plan, generate images, and prepare the
          preview automatically. Most image approvals and corrections should happen in Preview book, not here.
        </p>
        {draftIdFilter ? (
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href={`/admin/workflow?draftId=${draftIdFilter}`}
              className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
            >
              Back to workflow
            </Link>
          </div>
        ) : null}
      </div>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {actionError ? <p className="text-sm text-rose-600">{actionError}</p> : null}
      {previewError ? <p className="text-sm text-rose-600">{previewError}</p> : null}

      {!pages.length ? (
        <EmptyState title="No pages in queue" description="No story pages match this filter." />
      ) : (
        <div className="space-y-4">
          {Object.entries(groupedPages).map(([draftId, draftPages]) => (
            <section key={draftId} className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
              <h3 className="text-base font-semibold text-slate-900">Draft {draftId}</h3>
              <div className="mt-4 space-y-3">
                {draftPages.map((page) => (
                  <div
                    key={page.id}
                    className="rounded-2xl border border-slate-100 bg-slate-50 p-4"
                  >
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-900">Page {page.page_number}</p>
                        <p className="mt-1 text-sm text-slate-600">{page.scene_summary}</p>
                        <p className="mt-2 text-sm text-slate-500">Status: {page.image_status}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={previewingPageId === page.id}
                          onClick={() => void handlePreviewIllustration(page.id)}
                          className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_SECONDARY_BUTTON}`}
                        >
                          {preview?.story_page_id === page.id ? "Hide prompt" : "Preview prompt"}
                        </button>
                        {page.image_status === "prompt_ready" ? (
                          <button
                            type="button"
                            disabled={busyPageId === page.id}
                            onClick={() => void handleGenerateIllustration(page.id)}
                            className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_SECONDARY_BUTTON}`}
                          >
                            {busyPageId === page.id ? "Generating image..." : "Manual generate image"}
                          </button>
                        ) : null}
                      </div>
                    </div>
                    {preview?.story_page_id === page.id ? (
                      <div className="mt-4 space-y-3 rounded-2xl border border-indigo-100 bg-white p-4">
                        <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-600">
                          <span className="rounded-full bg-slate-100 px-3 py-1">Provider: {preview.provider}</span>
                          <span className="rounded-full bg-slate-100 px-3 py-1">
                            Model: {preview.provider_model || "Not configured"}
                          </span>
                          <span className="rounded-full bg-slate-100 px-3 py-1">
                            Ready: {preview.generation_ready ? "Yes" : "No"}
                          </span>
                          <span className="rounded-full bg-slate-100 px-3 py-1">
                            Live available: {preview.live_generation_available ? "Yes" : "No"}
                          </span>
                        </div>
                        <div className="grid gap-3 lg:grid-cols-2">
                          <div className="rounded-2xl bg-slate-50 p-3">
                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Scene package</p>
                            <p className="mt-2 text-sm text-slate-700">{preview.scene_summary}</p>
                            <p className="mt-2 text-sm text-slate-600">Location: {preview.location}</p>
                            <p className="text-sm text-slate-600">Mood: {preview.mood}</p>
                            <p className="text-sm text-slate-600">Characters: {preview.characters_present}</p>
                          </div>
                          <div className="rounded-2xl bg-slate-50 p-3">
                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Positive prompt</p>
                            <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{preview.positive_prompt}</p>
                          </div>
                        </div>
                        {preview.negative_prompt ? (
                          <div className="rounded-2xl bg-amber-50 p-3">
                            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Negative prompt</p>
                            <p className="mt-2 whitespace-pre-wrap text-sm text-amber-900">{preview.negative_prompt}</p>
                          </div>
                        ) : null}
                        {preview.reference_assets.length ? (
                          <div className="rounded-2xl bg-sky-50 p-3">
                            <p className="text-xs font-semibold uppercase tracking-wide text-sky-800">Reference assets</p>
                            <div className="mt-2 flex flex-wrap gap-2">
                              {preview.reference_assets.map((asset) => (
                                <span
                                  key={asset.id}
                                  className="rounded-full border border-sky-200 bg-white px-3 py-1 text-xs font-medium text-sky-900"
                                >
                                  {asset.reference_type}: {asset.name}
                                </span>
                              ))}
                            </div>
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AdminStoryPagesPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <AdminStoryPagesPageContent />
    </Suspense>
  );
}
