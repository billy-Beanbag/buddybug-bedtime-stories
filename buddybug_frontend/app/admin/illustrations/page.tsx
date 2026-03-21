"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { IllustrationQueueList } from "@/components/admin/IllustrationQueueList";
import { useAuth } from "@/context/AuthContext";
import { apiGet } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { AdminIllustrationSummary, EditorialStoryDraftRead, EditorialStoryPageRead, VisualReferenceAssetRead } from "@/lib/types";

interface IllustrationAssetRead {
  id: number;
  story_page_id: number;
  image_url: string;
  version_number: number;
  approval_status: string;
  provider: string;
  created_at: string;
  updated_at: string;
}

interface BookRead {
  id: number;
  story_draft_id: number;
  title: string;
  published: boolean;
  publication_status: string;
}

function enrichIllustrations(
  illustrations: AdminIllustrationSummary[],
  pages: EditorialStoryPageRead[],
  drafts: EditorialStoryDraftRead[],
  books: BookRead[],
  latestAssetsByPage: Map<number, IllustrationAssetRead | null>,
): AdminIllustrationSummary[] {
  const pagesById = new Map(pages.map((page) => [page.id, page]));
  const draftsById = new Map(drafts.map((draft) => [draft.id, draft]));
  const booksByDraftId = new Map(books.map((book) => [book.story_draft_id, book]));

  return illustrations.map((illustration) => {
    const page = pagesById.get(illustration.story_page_id);
    const storyDraftId = illustration.story_draft_id ?? page?.story_draft_id ?? null;
    const draft = storyDraftId ? draftsById.get(storyDraftId) : undefined;
    const book = storyDraftId ? booksByDraftId.get(storyDraftId) : undefined;
    const latestAsset = latestAssetsByPage.get(illustration.story_page_id) ?? null;

    return {
      ...illustration,
      story_draft_id: storyDraftId,
      story_draft_title: illustration.story_draft_title ?? draft?.title ?? book?.title ?? null,
      book_id: illustration.book_id ?? book?.id ?? null,
      published: illustration.published ?? book?.published ?? null,
      publication_status: illustration.publication_status ?? book?.publication_status ?? null,
      page_number: illustration.page_number ?? page?.page_number ?? null,
      scene_summary: illustration.scene_summary ?? page?.scene_summary ?? null,
      image_url: illustration.image_url ?? latestAsset?.image_url ?? null,
    };
  });
}

export default function AdminIllustrationsPage() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const draftIdFilter = searchParams.get("draftId");
  const bookIdFilter = searchParams.get("bookId");
  const [illustrations, setIllustrations] = useState<AdminIllustrationSummary[]>([]);
  const [referencesByPage, setReferencesByPage] = useState<Record<number, VisualReferenceAssetRead[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approvalStatus, setApprovalStatus] = useState("");

  async function loadIllustrations() {
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await apiGet<AdminIllustrationSummary[]>("/admin/illustrations/queue", {
        token,
        query: { approval_status: approvalStatus || undefined },
      });
      try {
        const uniquePageIds = Array.from(new Set(response.map((illustration) => illustration.story_page_id)));
        const [pages, latestAssets] = await Promise.all([
          Promise.all(
            uniquePageIds.map(async (storyPageId) => {
              try {
                return await apiGet<EditorialStoryPageRead>(`/story-pages/${storyPageId}`, { token });
              } catch {
                return null;
              }
            }),
          ),
          Promise.all(
            uniquePageIds.map(async (storyPageId) => {
            try {
              const versions = await apiGet<IllustrationAssetRead[]>(`/illustrations/by-page/${storyPageId}`, { token });
              return [storyPageId, versions[0] ?? null] as const;
            } catch {
              return [storyPageId, null] as const;
            }
            }),
          ),
        ]);

        const resolvedPages = pages.filter((page): page is EditorialStoryPageRead => page !== null);
        const uniqueDraftIds = Array.from(new Set(resolvedPages.map((page) => page.story_draft_id)));
        const [drafts, books, recommendedReferences] = await Promise.all([
          Promise.all(
            uniqueDraftIds.map(async (draftId) => {
              try {
                return await apiGet<EditorialStoryDraftRead>(`/story-drafts/${draftId}`, { token });
              } catch {
                return null;
              }
            }),
          ),
          Promise.all(
            uniqueDraftIds.map(async (draftId) => {
              try {
                return await apiGet<BookRead>(`/books/by-draft/${draftId}`, { token });
              } catch {
                return null;
              }
            }),
          ),
          Promise.all(
            uniquePageIds.map(async (storyPageId) => {
              try {
                const refs = await apiGet<VisualReferenceAssetRead[]>(`/admin/visual-references/recommended-for-page/${storyPageId}`, {
                  token,
                });
                return [storyPageId, refs] as const;
              } catch {
                return [storyPageId, []] as const;
              }
            }),
          ),
        ]);

        setIllustrations(
          enrichIllustrations(
            response,
            resolvedPages,
            drafts.filter((draft): draft is EditorialStoryDraftRead => draft !== null),
            books.filter((book): book is BookRead => book !== null),
            new Map(latestAssets),
          ),
        );
        setReferencesByPage(Object.fromEntries(recommendedReferences));
      } catch {
        setIllustrations(response);
        setReferencesByPage({});
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load illustration queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadIllustrations();
  }, [token, approvalStatus]);

  if (loading) {
    return <LoadingState message="Loading illustration queue..." />;
  }

  if (error) {
    return <EmptyState title="Unable to load illustrations" description={error} />;
  }

  const filteredIllustrations = illustrations.filter((illustration) => {
    if (draftIdFilter && String(illustration.story_draft_id ?? "") !== draftIdFilter) {
      return false;
    }
    if (bookIdFilter && String(illustration.book_id ?? "") !== bookIdFilter) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Image queue</h2>
          <p className="mt-1 text-sm text-slate-600">
            Support queue for troubleshooting generated images. Normal review should now happen in Preview book,
            where each image sits beside its page text.
          </p>
          {draftIdFilter || bookIdFilter ? (
            <p className="mt-2 text-sm text-indigo-700">
              Focused on
              {draftIdFilter ? ` draft ${draftIdFilter}` : ""}
              {bookIdFilter ? `${draftIdFilter ? " and" : ""} book ${bookIdFilter}` : ""}.{" "}
              <Link href="/admin/illustrations" className="font-medium underline-offset-4 hover:underline">
                Clear filter
              </Link>
            </p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <select
            value={approvalStatus}
            onChange={(event) => setApprovalStatus(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All statuses</option>
            <option value="generated">Generated</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <button
            type="button"
            onClick={() => void loadIllustrations()}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="rounded-3xl border border-indigo-100 bg-indigo-50/60 p-4">
        <p className="text-sm font-semibold text-indigo-900">Primary workflow</p>
        <p className="mt-1 text-sm text-indigo-800">
          Approve the draft, open the preview book, review each page image in context, and publish once every page
          is approved. Use this queue only if you need to inspect versions or manually recover a page.
        </p>
        {draftIdFilter ? (
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href={`/admin/workflow?draftId=${draftIdFilter}`}
              className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
            >
              Open workflow
            </Link>
            <Link
              href={`/admin/story-pages?draftId=${draftIdFilter}`}
              className="rounded-2xl border border-indigo-200 bg-white px-4 py-2 text-sm font-medium text-indigo-900"
            >
              Open page plan support
            </Link>
          </div>
        ) : null}
      </div>

      <IllustrationQueueList
        illustrations={filteredIllustrations}
        referencesByPage={referencesByPage}
        token={token}
        onUpdated={loadIllustrations}
      />
    </div>
  );
}
