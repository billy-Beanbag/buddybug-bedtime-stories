"use client";

import Link from "next/link";
import { Suspense, useMemo, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { ApiError, apiDelete, apiGet, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON, ADMIN_SECONDARY_BUTTON } from "@/lib/admin-styles";
import type {
  AdminBookSummary,
  AdminStoryIdeaSummary,
  EditorialStoryDraftRead,
  EditorialStoryPageRead,
} from "@/lib/types";

interface WorkflowIllustrationRead {
  id: number;
  story_page_id: number;
  approval_status: string;
  provider: string;
  version_number: number;
  image_url: string | null;
  created_at: string;
  updated_at: string;
}

interface WorkflowRecord {
  key: string;
  title: string;
  updatedAt: string;
  idea: AdminStoryIdeaSummary | null;
  draft: EditorialStoryDraftRead | null;
  pages: EditorialStoryPageRead[];
  latestIllustrations: WorkflowIllustrationRead[];
  book: AdminBookSummary | null;
}

const IDEA_LIMIT = 120;
const DRAFT_LIMIT = 120;
const PAGE_LIMIT = 300;
const ILLUSTRATION_LIMIT = 300;
const BOOK_LIMIT = 120;

function isPublished(book: AdminBookSummary | null) {
  return Boolean(book && (book.published || book.publication_status === "published"));
}

function needsDraftReview(draft: EditorialStoryDraftRead | null) {
  return Boolean(
    draft &&
      (draft.review_status === "draft_pending_review" ||
        draft.review_status === "review_pending" ||
        draft.review_status === "needs_revision"),
  );
}

function getStatusClasses(status: string | null | undefined) {
  if (!status) {
    return "bg-slate-100 text-slate-700";
  }
  if (
    status.includes("approved") ||
    status.includes("published") ||
    status.includes("selected") ||
    status === "ready"
  ) {
    return "bg-emerald-50 text-emerald-800";
  }
  if (status.includes("reject") || status.includes("archived")) {
    return "bg-rose-50 text-rose-800";
  }
  if (status.includes("pending") || status.includes("generated") || status.includes("revision")) {
    return "bg-amber-50 text-amber-800";
  }
  return "bg-slate-100 text-slate-700";
}

function getReaderHref(book: AdminBookSummary) {
  return isPublished(book) ? `/reader/${book.id}` : `/reader/${book.id}?preview=1`;
}

function getRecordKeyForDraft(draft: EditorialStoryDraftRead) {
  return draft.story_idea_id !== null ? `idea-${draft.story_idea_id}` : `draft-${draft.id}`;
}

function formatTimestamp(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.valueOf())) {
    return value;
  }
  return parsed.toLocaleString();
}

function stageSummary(record: WorkflowRecord) {
  const promptReadyPages = record.pages.filter((page) => page.image_status === "prompt_ready").length;
  const generatedPages = record.pages.filter((page) => page.image_status === "image_generated").length;
  const approvedPages = record.pages.filter((page) => page.image_status === "image_approved").length;
  const rejectedPages = record.pages.filter((page) => page.image_status === "image_rejected").length;
  const generatedIllustrations = record.latestIllustrations.filter(
    (illustration) => illustration.approval_status === "generated",
  ).length;
  const approvedIllustrations = record.latestIllustrations.filter(
    (illustration) => illustration.approval_status === "approved",
  ).length;
  const rejectedIllustrations = record.latestIllustrations.filter(
    (illustration) => illustration.approval_status === "rejected",
  ).length;

  return {
    promptReadyPages,
    generatedPages,
    approvedPages,
    rejectedPages,
    generatedIllustrations,
    approvedIllustrations,
    rejectedIllustrations,
  };
}

function getReleaseReadiness(record: WorkflowRecord) {
  if (!record.draft || record.pages.length === 0) {
    return {
      ready: false,
      reason: "Create a page plan before assembling a book.",
    };
  }

  const incompletePages = record.pages.filter((page) => page.image_status !== "image_approved");
  if (incompletePages.length > 0) {
    return {
      ready: false,
      reason: `Approved illustrations still needed for ${incompletePages.length} page${incompletePages.length === 1 ? "" : "s"}.`,
    };
  }

  return {
    ready: true,
    reason: "All planned pages have approved illustrations.",
  };
}

function getNextActionLabel(record: WorkflowRecord) {
  const summary = stageSummary(record);
  const releaseReadiness = getReleaseReadiness(record);

  if (record.idea?.status === "idea_pending") {
    return "Select or reject idea";
  }
  if (!record.draft && record.idea && (record.idea.status === "idea_selected" || record.idea.status === "converted_to_draft")) {
    return "Generate draft";
  }
  if (needsDraftReview(record.draft)) {
    return "Review draft";
  }
  if (record.draft?.review_status === "approved_for_illustration" && record.pages.length === 0) {
    return "Preparing page plan";
  }
  if (summary.promptReadyPages > 0 || summary.rejectedPages > 0) {
    return "Generate missing page images";
  }
  if (record.book && !isPublished(record.book) && !releaseReadiness.ready) {
    return "Review preview book";
  }
  if (!record.book && record.draft && record.pages.length > 0) {
    return "Build preview book";
  }
  if (summary.generatedIllustrations > 0 || summary.rejectedIllustrations > 0) {
    return "Review images in preview";
  }
  if (record.book && !isPublished(record.book) && releaseReadiness.ready) {
    return "Publish book";
  }
  if (record.book && isPublished(record.book)) {
    return "Published";
  }
  if (record.draft && record.pages.length > 0 && !releaseReadiness.ready) {
    return "Complete illustration approvals";
  }
  return "In progress";
}

function buildWorkflowRecords({
  ideas,
  drafts,
  pages,
  illustrations,
  books,
}: {
  ideas: AdminStoryIdeaSummary[];
  drafts: EditorialStoryDraftRead[];
  pages: EditorialStoryPageRead[];
  illustrations: WorkflowIllustrationRead[];
  books: AdminBookSummary[];
}) {
  const latestIllustrationByPage = new Map<number, WorkflowIllustrationRead>();
  for (const illustration of illustrations) {
    const existing = latestIllustrationByPage.get(illustration.story_page_id);
    if (
      !existing ||
      illustration.version_number > existing.version_number ||
      (illustration.version_number === existing.version_number && illustration.updated_at > existing.updated_at)
    ) {
      latestIllustrationByPage.set(illustration.story_page_id, illustration);
    }
  }

  const pagesByDraftId = new Map<number, EditorialStoryPageRead[]>();
  for (const page of pages) {
    const existing = pagesByDraftId.get(page.story_draft_id) ?? [];
    existing.push(page);
    pagesByDraftId.set(page.story_draft_id, existing);
  }
  for (const item of pagesByDraftId.values()) {
    item.sort((left, right) => left.page_number - right.page_number);
  }

  const draftByIdeaId = new Map<number, EditorialStoryDraftRead>();
  for (const draft of drafts) {
    if (draft.story_idea_id !== null) {
      draftByIdeaId.set(draft.story_idea_id, draft);
    }
  }

  const bookByDraftId = new Map<number, AdminBookSummary>();
  for (const book of books) {
    const existing = bookByDraftId.get(book.story_draft_id);
    if (!existing || book.updated_at > existing.updated_at) {
      bookByDraftId.set(book.story_draft_id, book);
    }
  }

  const records: WorkflowRecord[] = [];
  const seenKeys = new Set<string>();

  for (const idea of ideas) {
    const draft = draftByIdeaId.get(idea.id) ?? null;
    const draftPages = draft ? pagesByDraftId.get(draft.id) ?? [] : [];
    const latestIllustrations = draftPages
      .map((page) => latestIllustrationByPage.get(page.id) ?? null)
      .filter((illustration): illustration is WorkflowIllustrationRead => illustration !== null);
    const book = draft ? bookByDraftId.get(draft.id) ?? null : null;
    const key = `idea-${idea.id}`;

    records.push({
      key,
      title: book?.title ?? draft?.title ?? idea.title,
      updatedAt: book?.updated_at ?? draft?.updated_at ?? idea.created_at,
      idea,
      draft,
      pages: draftPages,
      latestIllustrations,
      book,
    });
    seenKeys.add(key);
    if (draft) seenKeys.add(`draft-${draft.id}`);
  }

  for (const draft of drafts) {
    const key = draft.story_idea_id !== null ? `idea-${draft.story_idea_id}` : `draft-${draft.id}`;
    if (seenKeys.has(key)) {
      continue;
    }
    const draftPages = pagesByDraftId.get(draft.id) ?? [];
    const latestIllustrations = draftPages
      .map((page) => latestIllustrationByPage.get(page.id) ?? null)
      .filter((illustration): illustration is WorkflowIllustrationRead => illustration !== null);
    const book = bookByDraftId.get(draft.id) ?? null;

    records.push({
      key,
      title: book?.title ?? draft.title,
      updatedAt: book?.updated_at ?? draft.updated_at,
      idea: null,
      draft,
      pages: draftPages,
      latestIllustrations,
      book,
    });
    seenKeys.add(key);
  }

  for (const book of books) {
    const key = `draft-${book.story_draft_id}`;
    if (seenKeys.has(key)) {
      continue;
    }
    records.push({
      key,
      title: book.title,
      updatedAt: book.updated_at,
      idea: null,
      draft: null,
      pages: [],
      latestIllustrations: [],
      book,
    });
  }

  return records.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
}

function StageBlock({
  title,
  status,
  detail,
}: {
  title: string;
  status: string;
  detail: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <div className={`mt-2 inline-flex rounded-full px-3 py-1 text-xs font-medium ${getStatusClasses(status)}`}>
        {status}
      </div>
      <p className="mt-2 text-sm text-slate-600">{detail}</p>
    </div>
  );
}

function AdminWorkflowPageContent() {
  const { token } = useAuth();
  const searchParams = useSearchParams();
  const draftIdFilter = searchParams.get("draftId");
  const ideaIdFilter = searchParams.get("ideaId");
  const bookIdFilter = searchParams.get("bookId");

  const [ideas, setIdeas] = useState<AdminStoryIdeaSummary[]>([]);
  const [drafts, setDrafts] = useState<EditorialStoryDraftRead[]>([]);
  const [pages, setPages] = useState<EditorialStoryPageRead[]>([]);
  const [illustrations, setIllustrations] = useState<WorkflowIllustrationRead[]>([]);
  const [books, setBooks] = useState<AdminBookSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [statusRecordKey, setStatusRecordKey] = useState<string | null>(null);
  const [statusDetail, setStatusDetail] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<"info" | "success" | "error" | null>(null);
  const [nextStepRecordKey, setNextStepRecordKey] = useState<string | null>(null);
  const [nextStepType, setNextStepType] = useState<"preview" | null>(null);
  const [query, setQuery] = useState("");
  const [view, setView] = useState<"all" | "needs_action" | "published" | "selected_only">("needs_action");

  async function loadWorkflow(options?: { silent?: boolean }) {
    if (!token) {
      return;
    }

    if (!options?.silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const [ideasResponse, draftsResponse, pagesResponse, illustrationsResponse, booksResponse] = await Promise.all([
        apiGet<AdminStoryIdeaSummary[]>("/story-ideas", { token, query: { limit: IDEA_LIMIT } }),
        apiGet<EditorialStoryDraftRead[]>("/story-drafts", { token, query: { limit: DRAFT_LIMIT } }),
        apiGet<EditorialStoryPageRead[]>("/story-pages", { token, query: { limit: PAGE_LIMIT } }),
        apiGet<WorkflowIllustrationRead[]>("/illustrations", { token, query: { limit: ILLUSTRATION_LIMIT } }),
        apiGet<AdminBookSummary[]>("/books", { token, query: { limit: BOOK_LIMIT } }),
      ]);
      setIdeas(ideasResponse);
      setDrafts(draftsResponse);
      setPages(pagesResponse);
      setIllustrations(illustrationsResponse);
      setBooks(booksResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load workflow progress");
    } finally {
      if (!options?.silent) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    void loadWorkflow();
  }, [token]);

  const workflowRecords = useMemo(
    () =>
      buildWorkflowRecords({
        ideas,
        drafts,
        pages,
        illustrations,
        books,
      }),
    [ideas, drafts, pages, illustrations, books],
  );

  const visibleRecords = useMemo(() => {
    return workflowRecords.filter((record) => {
      if (draftIdFilter) {
        const targetDraftId = Number(draftIdFilter);
        if (record.draft?.id !== targetDraftId && record.book?.story_draft_id !== targetDraftId) {
          return false;
        }
      }
      if (ideaIdFilter) {
        const targetIdeaId = Number(ideaIdFilter);
        if (record.idea?.id !== targetIdeaId && record.draft?.story_idea_id !== targetIdeaId) {
          return false;
        }
      }
      if (bookIdFilter) {
        const targetBookId = Number(bookIdFilter);
        if (record.book?.id !== targetBookId) {
          return false;
        }
      }

      if (view !== "all") {
        const ideaStatus = record.idea?.status;
        if (ideaStatus === "idea_pending" || ideaStatus === "idea_rejected") {
          return false;
        }
      }
      if (view === "selected_only") {
        const ideaStatus = record.idea?.status;
        return ideaStatus === "idea_selected" || ideaStatus === "converted_to_draft";
      }
      if (view === "published") {
        return isPublished(record.book);
      }
      if (view === "needs_action") {
        return !isPublished(record.book);
      }

      const normalizedQuery = query.trim().toLowerCase();
      if (normalizedQuery) {
        const searchTarget = [
          record.title,
          record.idea?.title,
          record.idea?.premise,
          record.draft?.summary,
          record.book?.title,
          record.idea?.status,
          record.draft?.review_status,
          record.book?.publication_status,
          record.idea ? `idea ${record.idea.id}` : "",
          record.draft ? `draft ${record.draft.id}` : "",
          record.book ? `book ${record.book.id}` : "",
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        if (!searchTarget.includes(normalizedQuery)) {
          return false;
        }
      }

      return true;
    });
  }, [workflowRecords, draftIdFilter, ideaIdFilter, bookIdFilter, query, view]);

  const BEDTIME_LANE = "bedtime_3_7";
  const ADVENTURE_LANE = "story_adventures_3_7";

  async function handleIdeaAction(
    ideaId: number,
    action: "select" | "reject",
    contentLaneKey?: string,
  ) {
    if (!token) return;
    setStatusRecordKey(`idea-${ideaId}`);
    setStatusTone("info");
    setStatusDetail(
      action === "reject"
        ? "Rejecting this idea..."
        : contentLaneKey === BEDTIME_LANE
          ? "Selecting as Bedtime..."
          : contentLaneKey === ADVENTURE_LANE
            ? "Selecting as Adventure..."
            : "Selecting this idea...",
    );
    setNextStepRecordKey(null);
    setNextStepType(null);
    setBusyKey(`idea-${ideaId}-${action}-${contentLaneKey ?? ""}`);
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
      setStatusTone("success");
      setStatusDetail("Refreshing workflow...");
      await loadWorkflow({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : `Unable to ${action} idea`);
      setStatusTone("error");
      setStatusDetail(action === "select" ? "Unable to select this idea." : "Unable to reject this idea.");
    } finally {
      setBusyKey(null);
    }
  }

  async function handleGenerateDraft(ideaId: number) {
    if (!token) {
      return;
    }
    setStatusRecordKey(`idea-${ideaId}`);
    setStatusTone("info");
    setStatusDetail("Generating a draft from this idea...");
    setNextStepRecordKey(null);
    setNextStepType(null);
    setBusyKey(`idea-${ideaId}-draft`);
    setMessage(null);
    setError(null);
    try {
      await apiPost("/story-drafts/generate", { story_idea_id: ideaId }, { token, timeoutMs: 150000 });
      setMessage("Draft generated from selected idea.");
      setStatusTone("success");
      setStatusDetail("Draft generated. Refreshing workflow...");
      await loadWorkflow({ silent: true });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unable to generate draft";
      const isAbort = msg.toLowerCase().includes("abort") || msg.toLowerCase().includes("timeout");
      setError(isAbort ? "Request timed out. Draft generation can take a couple of minutes online - please try again." : msg);
      setStatusTone("error");
      setStatusDetail("Unable to generate a draft for this idea.");
    } finally {
      setBusyKey(null);
    }
  }

  async function handleGeneratePlan(draft: EditorialStoryDraftRead) {
    if (!token) {
      return;
    }
    setStatusRecordKey(getRecordKeyForDraft(draft));
    setStatusTone("info");
    setStatusDetail("Generating a page-by-page illustration plan...");
    setNextStepRecordKey(null);
    setNextStepType(null);
    setBusyKey(`draft-${draft.id}-plan`);
    setMessage(null);
    setError(null);
    try {
      await apiPost(
        "/story-pages/generate-plan",
        {
          story_draft_id: draft.id,
          target_page_count: undefined,
          min_pages: 5,
          max_pages: 6,
        },
        { token },
      );
      await apiPost(
        "/workflows/generate-page-illustrations",
        {
          story_draft_id: draft.id,
        },
        { token, timeoutMs: 180_000 },
      );
      setMessage("Page plan generated and page images are now generating.");
      setStatusTone("success");
      setStatusDetail("Page plan generated and image generation started. Refreshing workflow...");
      await loadWorkflow({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate page plan");
      setStatusTone("error");
      setStatusDetail("Unable to generate a page plan for this draft.");
    } finally {
      setBusyKey(null);
    }
  }

  async function handleGeneratePageImages(record: WorkflowRecord) {
    if (!token || !record.draft) {
      return;
    }
    const pageIds = record.pages
      .filter((page) => page.image_status === "prompt_ready" || page.image_status === "image_rejected")
      .map((page) => page.id);
    setStatusRecordKey(record.key);
    setStatusTone("info");
    setStatusDetail("Starting page image generation...");
    setNextStepRecordKey(null);
    setNextStepType(null);
    setBusyKey(`draft-${record.draft.id}-images`);
    setMessage(null);
    setError(null);
    try {
      await apiPost(
        "/workflows/generate-page-illustrations",
        {
          story_draft_id: record.draft.id,
          page_ids: pageIds.length ? pageIds : undefined,
        },
        { token, timeoutMs: 180_000 },
      );
      setMessage("Page image generation started.");
      setStatusTone("success");
      setStatusDetail("Page image generation started. Refreshing workflow...");
      await loadWorkflow({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate page images");
      setStatusTone("error");
      setStatusDetail("Unable to start page image generation for this draft.");
    } finally {
      setBusyKey(null);
    }
  }

  async function handleAssembleBook(draft: EditorialStoryDraftRead) {
    if (!token) {
      return;
    }
    setStatusRecordKey(getRecordKeyForDraft(draft));
    setStatusTone("info");
    setStatusDetail("Assembling a preview book from the approved draft and pages...");
    setNextStepRecordKey(null);
    setNextStepType(null);
    setBusyKey(`draft-${draft.id}-assemble`);
    setMessage(null);
    setError(null);
    try {
      await apiPost(
        `/editorial/story-drafts/${draft.id}/build-preview`,
        undefined,
        { token, timeoutMs: 60_000 },
      );
      setMessage("Book preview assembled.");
      setStatusTone("success");
      setStatusDetail("Preview book assembled. Review the pages in context before publishing.");
      setNextStepRecordKey(getRecordKeyForDraft(draft));
      setNextStepType("preview");
      await loadWorkflow({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to assemble book");
      setStatusTone("error");
      setStatusDetail("Unable to assemble the preview book for this story.");
    } finally {
      setBusyKey(null);
    }
  }

  async function handlePublishBook(bookId: number, recordKey: string) {
    if (!token) {
      return;
    }
    setStatusRecordKey(recordKey);
    setStatusTone("info");
    setStatusDetail("Publishing this book...");
    setNextStepRecordKey(null);
    setNextStepType(null);
    setBusyKey(`book-${bookId}-publish`);
    setMessage(null);
    setError(null);
    try {
      await apiPost(`/books/${bookId}/publish`, undefined, { token });
      setMessage("Book published.");
      setStatusTone("success");
      setStatusDetail("Book published. Refreshing workflow...");
      await loadWorkflow({ silent: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to publish book");
      setStatusTone("error");
      setStatusDetail("Unable to publish this book.");
    } finally {
      setBusyKey(null);
    }
  }

  async function handleRemoveWorkflowRecord(record: WorkflowRecord) {
    if (!token) return;
    const bookId = record.book?.id;
    const draftId = record.draft?.id ?? record.book?.story_draft_id;
    const ideaId = record.idea?.id ?? record.draft?.story_idea_id ?? null;
    if (!bookId && !draftId && !ideaId) return;

    setStatusRecordKey(record.key);
    setStatusTone("info");
    setStatusDetail("Removing this workflow record...");
    setNextStepRecordKey(null);
    setNextStepType(null);
    setBusyKey(`remove-${record.key}`);
    setMessage(null);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (bookId) params.set("book_id", String(bookId));
      if (draftId) params.set("draft_id", String(draftId));
      if (ideaId) params.set("idea_id", String(ideaId));
      const qs = params.toString();
      // Root path (system router, registered first) - most reliable
      const paths: Array<{ method: "post" | "delete"; path: string }> = [
        { method: "post", path: `/delete-workflow-record?${qs}` },
        { method: "post", path: `/story-drafts/delete-workflow-record?${qs}` },
        { method: "delete", path: `/admin/workflow/record?${qs}` },
        { method: "delete", path: `/admin/workflow/record/remove?${qs}` },
        { method: "delete", path: `/admin/workflows/record?${qs}` },
      ];
      let lastErr: unknown;
      let succeeded = false;
      for (const { method, path } of paths) {
        try {
          if (method === "post") {
            await apiPost(path, undefined, { token });
          } else {
            await apiDelete(path, { token });
          }
          succeeded = true;
          break;
        } catch (e) {
          lastErr = e;
          const is404 = e instanceof ApiError && e.status === 404;
          const is405 = e instanceof ApiError && e.status === 405;
          if (!is404 && !is405) throw e;
        }
      }
      if (!succeeded && lastErr) throw lastErr;
      setMessage("Workflow record removed.");
      setStatusTone("success");
      setStatusDetail("Refreshing workflow...");
      await loadWorkflow({ silent: true });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unable to remove workflow record";
      setError(msg);
      setStatusTone("error");
      setStatusDetail("Unable to remove this record.");
    } finally {
      setBusyKey(null);
    }
  }

  if (loading) {
    return <LoadingState message="Loading story workflow..." />;
  }

  if (error && !workflowRecords.length) {
    return <EmptyState title="Unable to load workflow" description={error} />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Story workflow</h2>
            <p className="mt-1 text-sm text-slate-600">
              Follow each story from idea through review, illustration, assembly, and publication.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title or ID"
              className="min-w-56 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            />
            <select
              value={view}
              onChange={(event) =>
                setView(event.target.value as "selected_only" | "all" | "needs_action" | "published")
              }
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            >
              <option value="selected_only">Selected ideas only</option>
              <option value="needs_action">Needs action</option>
              <option value="all">All workflows</option>
              <option value="published">Published only</option>
            </select>
            <button
              type="button"
              onClick={() => void loadWorkflow()}
              className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
            >
              Refresh
            </button>
          </div>
        </div>
        {draftIdFilter || ideaIdFilter || bookIdFilter ? (
          <p className="mt-3 text-sm text-slate-500">
            Focused view:
            {draftIdFilter ? ` draft ${draftIdFilter}` : ""}
            {ideaIdFilter ? `${draftIdFilter ? " |" : ""} idea ${ideaIdFilter}` : ""}
            {bookIdFilter ? `${draftIdFilter || ideaIdFilter ? " |" : ""} book ${bookIdFilter}` : ""}
          </p>
        ) : null}
        {message ? <p className="mt-3 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-3 text-sm text-rose-600">{error}</p> : null}
      </section>

      {!visibleRecords.length ? (
        <EmptyState
          title="No workflow items found"
          description="Try a different search, switch the filter, or refresh the workflow view."
        />
      ) : (
        <div className="space-y-4">
          {visibleRecords.map((record) => {
            const summary = stageSummary(record);
            const nextAction = getNextActionLabel(record);
            const bookPublished = isPublished(record.book);
            const releaseReadiness = getReleaseReadiness(record);

            return (
              <section key={record.key} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-lg font-semibold text-slate-900">{record.title}</h3>
                      <span className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusClasses(nextAction)}`}>
                        {nextAction}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      {record.idea ? `Idea ${record.idea.id}` : "Idea unavailable"}
                      {record.draft ? ` • Draft ${record.draft.id}` : ""}
                      {record.book ? ` • Book ${record.book.id}` : ""}
                      {record.draft?.content_lane_key ? ` • ${record.draft.content_lane_key}` : ""}
                    </p>
                    <p className="mt-1 text-sm text-slate-500">Updated {formatTimestamp(record.updatedAt)}</p>
                    {record.idea?.premise ? <p className="mt-3 text-sm text-slate-600">{record.idea.premise}</p> : null}
                    {!record.idea?.premise && record.draft?.summary ? (
                      <p className="mt-3 text-sm text-slate-600">{record.draft.summary}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {record.idea ? (
                      <span className={`rounded-full px-3 py-2 text-sm font-medium ${getStatusClasses(record.idea.status)}`}>
                        {record.idea.status}
                      </span>
                    ) : null}
                    {record.draft ? (
                      <span className={`rounded-full px-3 py-2 text-sm font-medium ${getStatusClasses(record.draft.review_status)}`}>
                        {record.draft.review_status}
                      </span>
                    ) : null}
                    {record.book ? (
                      <span className={`rounded-full px-3 py-2 text-sm font-medium ${getStatusClasses(record.book.publication_status)}`}>
                        {record.book.publication_status}
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="mt-4 grid gap-3 xl:grid-cols-5">
                  <StageBlock
                    title="Idea"
                    status={record.idea?.status || "missing"}
                    detail={record.idea ? record.idea.title : "This workflow no longer has a linked story idea."}
                  />
                  <StageBlock
                    title="Draft"
                    status={record.draft?.review_status || "not_created"}
                    detail={
                      record.draft
                        ? `${record.draft.read_time_minutes} min read`
                        : record.idea
                          ? "Generate a draft after selecting the idea."
                          : "No draft is linked to this workflow yet."
                    }
                  />
                  <StageBlock
                    title="Page Plan"
                    status={
                      record.pages.length
                        ? `${record.pages.length} planned`
                        : record.draft?.review_status === "approved_for_illustration"
                          ? "ready_to_plan"
                          : "waiting"
                    }
                    detail={
                      record.pages.length
                        ? `${summary.promptReadyPages} still need images, ${summary.approvedPages} already approved for release`
                        : "No page-by-page plan created yet."
                    }
                  />
                  <StageBlock
                    title="Page Images"
                    status={
                      record.latestIllustrations.length
                        ? `${summary.approvedIllustrations} approved`
                        : record.pages.length
                          ? "not_generated"
                          : "waiting"
                    }
                    detail={
                      record.latestIllustrations.length
                        ? `${summary.generatedIllustrations} waiting for preview review, ${summary.rejectedIllustrations} rejected`
                        : "No latest illustration versions exist for these pages yet."
                    }
                  />
                  <StageBlock
                    title="Book"
                    status={record.book?.publication_status || "not_assembled"}
                    detail={
                      record.book
                        ? bookPublished
                          ? "Published and visible in the reader."
                          : releaseReadiness.ready
                            ? "Preview is ready and can now be published."
                            : "Preview the book, review each page image in context, then publish when all pages are approved."
                        : "Build the preview book to review text and illustrations together."
                    }
                  />
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {record.idea?.status === "idea_pending" ? (
                    <>
                      <button
                        type="button"
                        disabled={Boolean(busyKey?.startsWith(`idea-${record.idea.id}`))}
                        onClick={() => void handleIdeaAction(record.idea!.id, "select", BEDTIME_LANE)}
                        className="rounded-2xl bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-800 disabled:opacity-60"
                        title="Select as Bedtime story (calm, gentle, 3–7)"
                      >
                        Select as Bedtime
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(busyKey?.startsWith(`idea-${record.idea.id}`))}
                        onClick={() => void handleIdeaAction(record.idea!.id, "select", ADVENTURE_LANE)}
                        className="rounded-2xl bg-amber-50 px-4 py-2 text-sm font-medium text-amber-800 disabled:opacity-60"
                        title="Select as Adventure story (playful, plot-led, 3-7)"
                      >
                        Select as Adventure 3-7
                      </button>
                      <button
                        type="button"
                        disabled={Boolean(busyKey?.startsWith(`idea-${record.idea.id}`))}
                        onClick={() => void handleIdeaAction(record.idea!.id, "reject")}
                        className="rounded-2xl bg-rose-50 px-4 py-2 text-sm font-medium text-rose-800 disabled:opacity-60"
                      >
                        Reject idea
                      </button>
                    </>
                  ) : null}

                  {!record.draft && record.idea && (record.idea.status === "idea_selected" || record.idea.status === "converted_to_draft") ? (
                    <button
                      type="button"
                      disabled={busyKey === `idea-${record.idea.id}-draft`}
                      onClick={() => void handleGenerateDraft(record.idea!.id)}
                      className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
                    >
                      {busyKey === `idea-${record.idea.id}-draft` ? "Generating draft..." : "Generate draft"}
                    </button>
                  ) : null}

                  {record.draft ? (
                    <Link
                      href={`/admin/drafts/${record.draft.id}`}
                      className={`rounded-2xl px-4 py-2 text-sm font-medium ${ADMIN_SECONDARY_BUTTON}`}
                    >
                      Review draft
                    </Link>
                  ) : null}

                  {record.draft?.review_status === "approved_for_illustration" && record.pages.length === 0 ? (
                    <button
                      type="button"
                      disabled={busyKey === `draft-${record.draft.id}-plan`}
                      onClick={() => void handleGeneratePlan(record.draft!)}
                      className="rounded-2xl bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-800 disabled:opacity-60"
                    >
                      {busyKey === `draft-${record.draft.id}-plan` ? "Generating page plan..." : "Generate page plan"}
                    </button>
                  ) : null}

                  {record.draft && (summary.promptReadyPages > 0 || summary.rejectedPages > 0) ? (
                    <button
                      type="button"
                      disabled={busyKey === `draft-${record.draft.id}-images`}
                      onClick={() => void handleGeneratePageImages(record)}
                      className="rounded-2xl bg-violet-50 px-4 py-2 text-sm font-medium text-violet-800 disabled:opacity-60"
                    >
                      {busyKey === `draft-${record.draft.id}-images` ? "Starting page images..." : "Generate page images"}
                    </button>
                  ) : null}

                  {record.draft && record.pages.length > 0 && !bookPublished ? (
                    <button
                      type="button"
                      disabled={busyKey === `draft-${record.draft.id}-assemble`}
                      onClick={() => void handleAssembleBook(record.draft!)}
                      className="rounded-2xl bg-amber-50 px-4 py-2 text-sm font-medium text-amber-800 disabled:opacity-60"
                    >
                      {busyKey === `draft-${record.draft.id}-assemble`
                        ? "Assembling preview book..."
                        : record.book
                          ? "Refresh preview book"
                          : "Assemble preview book"}
                    </button>
                  ) : null}

                  {record.book && !bookPublished ? (
                    <>
                      <Link
                        href={getReaderHref(record.book)}
                        className={`rounded-2xl px-4 py-2 text-sm font-medium ${
                          nextStepRecordKey === record.key && nextStepType === "preview"
                            ? "border border-teal-200 bg-teal-100 text-teal-900 shadow-sm"
                            : "bg-teal-50 text-teal-800"
                        }`}
                      >
                        {nextStepRecordKey === record.key && nextStepType === "preview"
                          ? "Preview ready - open book"
                          : "Preview book"}
                      </Link>
                      <span className="rounded-2xl bg-teal-50 px-4 py-2 text-sm text-teal-900">
                        Primary review happens in Preview book.
                      </span>
                      <button
                        type="button"
                        disabled={!releaseReadiness.ready || busyKey === `book-${record.book.id}-publish`}
                        onClick={() => void handlePublishBook(record.book!.id, record.key)}
                        className="rounded-2xl bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-800 disabled:opacity-60"
                        title={!releaseReadiness.ready ? releaseReadiness.reason : undefined}
                      >
                        {busyKey === `book-${record.book.id}-publish` ? "Publishing..." : "Publish book"}
                      </button>
                    </>
                  ) : null}

                  {record.pages.length > 0 ? (
                    <Link
                      href={`/admin/story-pages?draftId=${record.draft?.id ?? ""}`}
                      className="rounded-2xl border border-sky-200 bg-white px-4 py-2 text-sm font-medium text-sky-900"
                    >
                      Page plan support
                    </Link>
                  ) : null}

                  {record.latestIllustrations.length > 0 || summary.promptReadyPages > 0 || summary.rejectedPages > 0 ? (
                    <Link
                      href={`/admin/illustrations?draftId=${record.draft?.id ?? ""}${record.book ? `&bookId=${record.book.id}` : ""}`}
                      className="rounded-2xl border border-violet-200 bg-white px-4 py-2 text-sm font-medium text-violet-900"
                    >
                      Technical image queue
                    </Link>
                  ) : null}

                  {statusRecordKey === record.key && statusDetail ? (
                    <span
                      className={`rounded-2xl px-4 py-2 text-sm ${
                        statusTone === "error"
                          ? "bg-rose-50 text-rose-800"
                          : statusTone === "success"
                            ? "bg-emerald-50 text-emerald-800"
                            : "bg-indigo-50 text-indigo-800"
                      }`}
                    >
                      {statusDetail}
                    </span>
                  ) : null}

                  {!releaseReadiness.ready && record.draft && record.pages.length > 0 ? (
                    <span className="rounded-2xl bg-amber-50 px-4 py-2 text-sm text-amber-900">
                      {releaseReadiness.reason}
                    </span>
                  ) : null}

                  {record.book ? (
                    <Link
                      href={getReaderHref(record.book)}
                      className="rounded-2xl bg-slate-100 px-4 py-2 text-sm font-medium text-slate-800"
                    >
                      {bookPublished ? "View published book" : "Open reader"}
                    </Link>
                  ) : null}

                  <button
                    type="button"
                    disabled={busyKey === `remove-${record.key}`}
                    onClick={() => void handleRemoveWorkflowRecord(record)}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:opacity-60"
                    title="Remove this card and all associated data (book, draft, idea)"
                  >
                    {busyKey === `remove-${record.key}` ? "Removing…" : "Remove"}
                  </button>
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function AdminWorkflowPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <AdminWorkflowPageContent />
    </Suspense>
  );
}
