"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ActivityFeed } from "@/components/admin/ActivityFeed";
import { EditorialAssetsPanel } from "@/components/admin/EditorialAssetsPanel";
import { EditorialProjectEditor } from "@/components/admin/EditorialProjectEditor";
import { DraftVersionHistory } from "@/components/admin/DraftVersionHistory";
import { ManualStoryDraftForm } from "@/components/admin/ManualStoryDraftForm";
import { ManualStoryPagesEditor } from "@/components/admin/ManualStoryPagesEditor";
import { PageVersionHistory } from "@/components/admin/PageVersionHistory";
import { PreviewBookButton } from "@/components/admin/PreviewBookButton";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost, resolveApiUrl } from "@/lib/api";
import type {
  EditorialAssetRead,
  EditorialProjectDraftResponse,
  EditorialQualityRunResponse,
  EditorialProjectRead,
  PreviewBookResponse,
  VisualReferenceAssetRead,
} from "@/lib/types";

export default function EditorialProjectDetailPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = Number(params.projectId);
  const { token, isEditor } = useAuth();
  const [project, setProject] = useState<EditorialProjectRead | null>(null);
  const [draftState, setDraftState] = useState<EditorialProjectDraftResponse | null>(null);
  const [assets, setAssets] = useState<EditorialAssetRead[]>([]);
  const [preview, setPreview] = useState<PreviewBookResponse | null>(null);
  const [qualityResult, setQualityResult] = useState<EditorialQualityRunResponse | null>(null);
  const [projectReferences, setProjectReferences] = useState<VisualReferenceAssetRead[]>([]);
  const [draftReferences, setDraftReferences] = useState<VisualReferenceAssetRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadProjectState() {
    if (!token || !projectId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [projectResponse, draftResponse, assetsResponse] = await Promise.all([
        apiGet<EditorialProjectRead>(`/editorial/projects/${projectId}`, { token }),
        apiGet<EditorialProjectDraftResponse>(`/editorial/projects/${projectId}/draft`, { token }),
        apiGet<EditorialAssetRead[]>(`/editorial/projects/${projectId}/assets`, { token }),
      ]);
      const [projectRefsResponse, draftRefsResponse] = await Promise.all([
        apiGet<VisualReferenceAssetRead[]>("/admin/visual-references/by-target", {
          token,
          query: { target_type: "editorial_project", target_id: projectId },
        }),
        draftResponse.draft
          ? apiGet<VisualReferenceAssetRead[]>("/admin/visual-references/by-target", {
              token,
              query: { target_type: "story_draft", target_id: draftResponse.draft.id },
            })
          : Promise.resolve([]),
      ]);
      setProject(projectResponse);
      setDraftState(draftResponse);
      setAssets(assetsResponse);
      setProjectReferences(projectRefsResponse);
      setDraftReferences(draftRefsResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load editorial project");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadProjectState();
  }, [projectId, token]);

  if (!isEditor) {
    return <EmptyState title="Editorial access required" description="Only editor and admin users can open this area." />;
  }

  if (loading) {
    return <LoadingState message="Loading editorial workspace..." />;
  }

  if (error || !project || !draftState) {
    return <EmptyState title="Unable to load editorial workspace" description={error || "Project not found."} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm text-slate-500">Editorial project</p>
          <h2 className="text-2xl font-semibold text-slate-900">{project.title}</h2>
        </div>
        <Link
          href="/admin/editorial"
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
        >
          Back to list
        </Link>
      </div>

      <EditorialProjectEditor
        project={project}
        onSave={async (payload) => {
          if (!token) {
            return;
          }
          const updated = await apiPatch<EditorialProjectRead>(`/editorial/projects/${projectId}`, payload, { token });
          setProject(updated);
        }}
        onReadyForPublish={async () => {
          if (!token) {
            return;
          }
          const updated = await apiPost<EditorialProjectRead>(`/editorial/projects/${projectId}/ready-for-publish`, undefined, {
            token,
          });
          setProject(updated);
        }}
        onPublish={async () => {
          if (!token) {
            return;
          }
          const published = await apiPost<PreviewBookResponse>(`/editorial/projects/${projectId}/publish`, undefined, {
            token,
          });
          setPreview(published);
          await loadProjectState();
        }}
      />

      <ManualStoryDraftForm
        draft={draftState.draft}
        projectId={project.id}
        projectAgeBand={project.age_band}
        projectLanguage={project.language}
        onCreate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPost("/editorial/story-drafts", payload, { token });
          await loadProjectState();
        }}
        onSave={async (payload) => {
          if (!token || !draftState.draft) {
            return;
          }
          await apiPatch(`/editorial/story-drafts/${draftState.draft.id}`, payload, { token });
          await loadProjectState();
        }}
      />

      {draftState.draft ? (
        <DraftVersionHistory
          draftId={draftState.draft.id}
          token={token}
          onRolledBack={async () => {
            await loadProjectState();
          }}
        />
      ) : null}

      {draftState.draft ? (
        <ManualStoryPagesEditor
          draftId={draftState.draft.id}
          pages={draftState.pages}
          onCreate={async (payload) => {
            if (!token) {
              return;
            }
            await apiPost("/editorial/story-pages", payload, { token });
            await loadProjectState();
          }}
          onSave={async (pageId, payload) => {
            if (!token) {
              return;
            }
            await apiPatch(`/editorial/story-pages/${pageId}`, payload, { token });
            await loadProjectState();
          }}
        />
      ) : null}

      {draftState.pages.length ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {draftState.pages.map((page) => (
            <PageVersionHistory
              key={page.id}
              pageId={page.id}
              pageNumber={page.page_number}
              token={token}
              onRolledBack={async () => {
                await loadProjectState();
              }}
            />
          ))}
        </div>
      ) : null}

      <EditorialAssetsPanel
        projectId={project.id}
        assets={assets}
        onCreate={async (payload) => {
          if (!token) {
            return;
          }
          await apiPost(`/editorial/projects/${projectId}/assets`, payload, { token });
          await loadProjectState();
        }}
        onToggleActive={async (asset) => {
          if (!token) {
            return;
          }
          await apiPatch(`/editorial/assets/${asset.id}`, { is_active: true }, { token });
          await loadProjectState();
        }}
      />

      {projectReferences.length || draftReferences.length ? (
        <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Linked visual references</h3>
              <p className="mt-1 text-sm text-slate-600">
                Reusable style boards and reference images currently attached to this project or its draft.
              </p>
            </div>
            <Link
              href="/admin/visual-references"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-900"
            >
              Manage references
            </Link>
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <h4 className="text-sm font-semibold text-slate-900">Project references</h4>
              {projectReferences.length ? (
                projectReferences.map((asset) => (
                  <div key={asset.id} className="flex gap-3 rounded-2xl bg-white p-3">
                    <div className="h-16 w-16 overflow-hidden rounded-xl bg-slate-100">
                      <img src={resolveApiUrl(asset.image_url)} alt={asset.name} className="h-full w-full object-cover" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900">{asset.name}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {asset.reference_type} {asset.language ? `• ${asset.language}` : ""}
                      </p>
                      {asset.prompt_notes ? <p className="mt-2 text-xs text-slate-600">{asset.prompt_notes}</p> : null}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-600">No linked references yet.</p>
              )}
            </div>
            <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <h4 className="text-sm font-semibold text-slate-900">Draft references</h4>
              {draftReferences.length ? (
                draftReferences.map((asset) => (
                  <div key={asset.id} className="flex gap-3 rounded-2xl bg-white p-3">
                    <div className="h-16 w-16 overflow-hidden rounded-xl bg-slate-100">
                      <img src={resolveApiUrl(asset.image_url)} alt={asset.name} className="h-full w-full object-cover" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900">{asset.name}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {asset.reference_type} {asset.language ? `• ${asset.language}` : ""}
                      </p>
                      {asset.prompt_notes ? <p className="mt-2 text-xs text-slate-600">{asset.prompt_notes}</p> : null}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-600">No linked references yet.</p>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {draftState.draft ? (
        <div className="grid gap-4 xl:grid-cols-2">
          <PreviewBookButton
            label="Build preview book"
            onRun={async () => {
              if (!token || !draftState.draft) {
                return;
              }
              const builtPreview = await apiPost<PreviewBookResponse>(
                `/editorial/story-drafts/${draftState.draft.id}/build-preview`,
                undefined,
                { token },
              );
              setPreview(builtPreview);
              await loadProjectState();
            }}
            preview={preview}
          />

          <div className="space-y-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Quality checks</h3>
            <button
              type="button"
              onClick={() => {
                if (!token || !draftState.draft) {
                  return;
                }
                void apiPost<EditorialQualityRunResponse>(
                  `/editorial/story-drafts/${draftState.draft.id}/run-quality`,
                  undefined,
                  { token },
                ).then((response) => setQualityResult(response));
              }}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
            >
              Run quality checks
            </button>
            {draftState.preview_book ? (
              <p className="text-sm text-slate-600">
                Existing preview book #{draftState.preview_book.id} is ready with status{" "}
                <span className="font-medium text-slate-900">{draftState.preview_book.publication_status}</span>.
              </p>
            ) : (
              <p className="text-sm text-slate-600">No preview book has been built yet.</p>
            )}
            {qualityResult ? (
              <div className="space-y-2">
                {[...qualityResult.draft_checks, ...qualityResult.page_checks].map((check) => (
                  <div key={check.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs">
                    <p className="font-medium text-slate-900">
                      {check.check_type} • {check.status}
                    </p>
                    <p className="mt-1 text-slate-600">{check.summary}</p>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      <ActivityFeed token={token} entityType="editorial_project" entityId={project.id} />
    </div>
  );
}
