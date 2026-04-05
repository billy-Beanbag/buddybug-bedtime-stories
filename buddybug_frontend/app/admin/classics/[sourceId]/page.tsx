"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type {
  ClassicAdaptationDraftRead,
  ClassicDraftBundleResponse,
  ClassicSourceRead,
} from "@/lib/types";

type SceneSeedNote = {
  sceneIndex: number;
  label: string;
  excerptAnchor: string;
  featuredCharacters: string[];
  setting: string;
  mood: string;
  keyVisualAction: string;
  illustrationNotes: string;
};

type RouteProps = {
  params: Promise<{ sourceId: string }>;
};

const ADAPTATION_INTENSITY_OPTIONS = [
  {
    value: "minimal",
    label: "Minimal",
    description: "Almost no additions, just tiny magical witness moments.",
  },
  {
    value: "light",
    label: "Light",
    description: "A few brief Buddybug cameos in natural places.",
  },
  {
    value: "gentle_plus",
    label: "Gentle Plus",
    description: "Still restrained, but allows a little more connective magic.",
  },
] as const;

function parseBulletList(value: string | null | undefined): string[] {
  if (!value) {
    return [];
  }
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/^[-*]\s*/, "").trim())
    .filter(Boolean);
}

function parseWarnings(value: string | null | undefined): string[] {
  if (!value) {
    return [];
  }
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => String(item).trim()).filter(Boolean);
    }
  } catch {
    return parseBulletList(value);
  }
  return [];
}

function parseSceneSeedNotes(value: string | null | undefined): SceneSeedNote[] {
  if (!value) {
    return [];
  }
  try {
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .map((item) => {
        if (!item || typeof item !== "object") {
          return null;
        }
        const candidate = item as Partial<SceneSeedNote>;
        return {
          sceneIndex: Number(candidate.sceneIndex ?? 0),
          label: String(candidate.label ?? "").trim(),
          excerptAnchor: String(candidate.excerptAnchor ?? "").trim(),
          featuredCharacters: Array.isArray(candidate.featuredCharacters)
            ? candidate.featuredCharacters.map((entry) => String(entry).trim()).filter(Boolean)
            : [],
          setting: String(candidate.setting ?? "").trim(),
          mood: String(candidate.mood ?? "").trim(),
          keyVisualAction: String(candidate.keyVisualAction ?? "").trim(),
          illustrationNotes: String(candidate.illustrationNotes ?? "").trim(),
        } satisfies SceneSeedNote;
      })
      .filter((item): item is SceneSeedNote => Boolean(item && item.label));
  } catch {
    return [];
  }
}

function validationToneClasses(status: string): string {
  if (status === "accepted") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (status === "accepted_with_warnings") {
    return "border-amber-200 bg-amber-50 text-amber-900";
  }
  return "border-rose-200 bg-rose-50 text-rose-900";
}

export default function AdminClassicDetailPage({ params }: RouteProps) {
  const { token } = useAuth();
  const [sourceId, setSourceId] = useState<number | null>(null);
  const [source, setSource] = useState<ClassicSourceRead | null>(null);
  const [drafts, setDrafts] = useState<ClassicAdaptationDraftRead[]>([]);
  const [bundle, setBundle] = useState<ClassicDraftBundleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [editorNotes, setEditorNotes] = useState("");
  const [adaptationIntensity, setAdaptationIntensity] = useState("light");

  useEffect(() => {
    void params.then((value) => setSourceId(Number(value.sourceId)));
  }, [params]);

  const latestDraft = useMemo(() => drafts[0] ?? null, [drafts]);
  const cameoItems = useMemo(() => parseBulletList(bundle?.adaptation.cameo_insertions_summary), [bundle]);
  const adaptationNotes = useMemo(() => parseBulletList(bundle?.adaptation.adaptation_notes), [bundle]);
  const validationWarnings = useMemo(() => parseWarnings(bundle?.adaptation.validation_warnings_json), [bundle]);
  const sceneSeedNotes = useMemo(() => parseSceneSeedNotes(bundle?.adaptation.scene_seed_notes_json), [bundle]);

  async function loadPage(currentSourceId: number) {
    if (!token) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const sourceResponse = await apiGet<ClassicSourceRead>(`/classics/sources/${currentSourceId}`, { token });
      const draftResponse = await apiGet<ClassicAdaptationDraftRead[]>("/classics/drafts", {
        token,
        query: { classic_source_id: currentSourceId, limit: 20 },
      });
      setSource(sourceResponse);
      setDrafts(draftResponse);
      const newest = draftResponse[0];
      if (newest) {
        const draftBundle = await apiGet<ClassicDraftBundleResponse>(`/classics/drafts/${newest.id}`, { token, timeoutMs: 90_000 });
        setBundle(draftBundle);
        setEditorNotes(draftBundle.adaptation.editor_notes || "");
        setAdaptationIntensity(draftBundle.adaptation.adaptation_intensity || "light");
      } else {
        setBundle(null);
        setEditorNotes("");
        setAdaptationIntensity("light");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load classic");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!sourceId) {
      return;
    }
    void loadPage(sourceId);
  }, [sourceId, token]);

  async function runAction(actionKey: string, fn: () => Promise<void>) {
    setWorking(actionKey);
    setError(null);
    setMessage(null);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setWorking(null);
    }
  }

  if (loading || sourceId === null) {
    return <LoadingState message="Loading classic source..." />;
  }

  if (!source) {
    return <EmptyState title="Classic source not found" description={error || "The requested classic source could not be loaded."} />;
  }

  return (
    <div className="space-y-5">
      <section className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <Link href="/admin/classics" className="text-sm font-medium text-indigo-700">
              Back to classics
            </Link>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">{source.title}</h2>
            <p className="mt-2 text-sm text-slate-600">{source.source_url}</p>
            <p className="mt-3 text-xs text-slate-500">
              {source.source_author || "Unknown author"} • {source.public_domain_verified ? "public domain verified" : "verification still required"} •{" "}
              status: {source.import_status}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() =>
                void runAction("archive-source", async () => {
                  if (!token) {
                    return;
                  }
                  await apiPost(`/classics/sources/${source.id}/archive`, undefined, { token });
                  setMessage("Classic source archived.");
                  await loadPage(source.id);
                })
              }
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
            >
              {working === "archive-source" ? "Archiving..." : "Archive source"}
            </button>
            <button
              type="button"
              onClick={() =>
                void runAction("toggle-verify", async () => {
                  if (!token) {
                    return;
                  }
                  await apiPatch(
                    `/classics/sources/${source.id}`,
                    { public_domain_verified: !source.public_domain_verified },
                    { token },
                  );
                  setMessage(source.public_domain_verified ? "Verification removed." : "Public-domain verification saved.");
                  await loadPage(source.id);
                })
              }
              className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
            >
              {source.public_domain_verified ? "Remove verification" : "Mark as verified"}
            </button>
          </div>
        </div>
      </section>

      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <section className="grid gap-5 xl:grid-cols-[1.05fr,0.95fr]">
        <div className="space-y-5">
          <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">Imported source text</h3>
                <p className="mt-1 text-sm text-slate-600">This remains internal-only and is never visible to readers.</p>
              </div>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700">
                {source.source_text.split(/\s+/).filter(Boolean).length} words
              </span>
            </div>
            <div className="mt-4 max-h-[32rem] overflow-y-auto rounded-2xl bg-slate-50 p-4 text-sm leading-7 text-slate-700 whitespace-pre-wrap">
              {source.source_text}
            </div>
          </div>

          {bundle ? (
            <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{bundle.adaptation.adapted_title}</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Review the adapted text before and after illustrations. The original classic should still feel materially intact.
                  </p>
                </div>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700">
                  {bundle.adaptation.review_status}
                </span>
              </div>
              <div className="mt-4 max-h-[32rem] overflow-y-auto rounded-2xl bg-slate-50 p-4 text-sm leading-7 text-slate-700 whitespace-pre-wrap">
                {bundle.adaptation.adapted_text}
              </div>
            </div>
          ) : null}
        </div>

        <div className="space-y-5">
          <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900">Editorial pipeline</h3>
            <p className="mt-1 text-sm text-slate-600">Imported classic → adapted draft → illustrations → review → publish.</p>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <label className="block text-sm font-semibold text-slate-900" htmlFor="classic-adaptation-intensity">
                Adaptation intensity
              </label>
              <select
                id="classic-adaptation-intensity"
                value={adaptationIntensity}
                onChange={(event) => setAdaptationIntensity(event.target.value)}
                disabled={Boolean(working)}
                className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
              >
                {ADAPTATION_INTENSITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="mt-2 text-xs leading-6 text-slate-600">
                {ADAPTATION_INTENSITY_OPTIONS.find((option) => option.value === adaptationIntensity)?.description}
              </p>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={!source.public_domain_verified || Boolean(working)}
                onClick={() =>
                  void runAction("adapt", async () => {
                    if (!token) {
                      return;
                    }
                    await apiPost(
                      `/classics/sources/${source.id}/adapt`,
                      {
                        age_band: "3-7",
                        content_lane_key: "bedtime_3_7",
                        language: "en",
                        adaptation_intensity: adaptationIntensity,
                        min_pages: 5,
                        max_pages: 6,
                      },
                      { token, timeoutMs: 180_000 },
                    );
                    setMessage("Buddybug classic draft created.");
                    await loadPage(source.id);
                  })
                }
                className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
              >
                {working === "adapt" ? "Creating draft..." : "Create Buddybug Draft"}
              </button>
              {latestDraft ? (
                <>
                  <button
                    type="button"
                    disabled={Boolean(working)}
                    onClick={() =>
                      void runAction("preview", async () => {
                        if (!token) {
                          return;
                        }
                        await apiPost(`/classics/drafts/${latestDraft.id}/preview-book`, undefined, {
                          token,
                          timeoutMs: 90_000,
                        });
                        setMessage("Preview book rebuilt.");
                        await loadPage(source.id);
                      })
                    }
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
                  >
                    {working === "preview" ? "Rebuilding..." : "Rebuild preview"}
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(working)}
                    onClick={() =>
                      void runAction("illustrations", async () => {
                        if (!token) {
                          return;
                        }
                        await apiPost(`/classics/drafts/${latestDraft.id}/generate-illustrations`, undefined, {
                          token,
                          timeoutMs: 240_000,
                        });
                        setMessage("Illustrations generated for the current classic draft.");
                        await loadPage(source.id);
                      })
                    }
                    className="rounded-2xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm font-medium text-indigo-900"
                  >
                    {working === "illustrations" ? "Generating..." : "Generate illustrations"}
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(working)}
                    onClick={() =>
                      void runAction("approve", async () => {
                        if (!token) {
                          return;
                        }
                        await apiPost(
                          `/classics/drafts/${latestDraft.id}/approve`,
                          { editor_notes: editorNotes || null },
                          { token, timeoutMs: 90_000 },
                        );
                        setMessage("Classic draft approved for publish.");
                        await loadPage(source.id);
                      })
                    }
                    className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900"
                  >
                    {working === "approve" ? "Approving..." : "Approve"}
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(working)}
                    onClick={() =>
                      void runAction("publish", async () => {
                        if (!token) {
                          return;
                        }
                        await apiPost(`/classics/drafts/${latestDraft.id}/publish`, undefined, {
                          token,
                          timeoutMs: 180_000,
                        });
                        setMessage("Classic published to the live library.");
                        await loadPage(source.id);
                      })
                    }
                    className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900"
                  >
                    {working === "publish" ? "Publishing..." : "Publish to library"}
                  </button>
                  <button
                    type="button"
                    disabled={Boolean(working)}
                    onClick={() =>
                      void runAction("archive-draft", async () => {
                        if (!token) {
                          return;
                        }
                        await apiPost(`/classics/drafts/${latestDraft.id}/archive`, undefined, { token });
                        setMessage("Classic draft archived.");
                        await loadPage(source.id);
                      })
                    }
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
                  >
                    {working === "archive-draft" ? "Archiving..." : "Archive draft"}
                  </button>
                </>
              ) : null}
            </div>
          </div>

          {bundle ? (
            <>
              <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900">Review insights</h3>
                <div className="mt-3 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Intensity</p>
                    <p className="mt-2 text-sm font-medium text-slate-900">{bundle.adaptation.adaptation_intensity}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Validation</p>
                    <span
                      className={`mt-2 inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${validationToneClasses(bundle.adaptation.validation_status)}`}
                    >
                      {bundle.adaptation.validation_status.replaceAll("_", " ")}
                    </span>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Scene seeds</p>
                    <p className="mt-2 text-sm font-medium text-slate-900">{sceneSeedNotes.length} planned scene notes</p>
                  </div>
                </div>

                <h4 className="mt-5 text-sm font-semibold text-slate-900">Cameo insertion notes</h4>
                {cameoItems.length > 0 ? (
                  <div className="mt-2 space-y-2">
                    {cameoItems.map((item) => (
                      <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-7 text-slate-700">
                        {item}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">No cameo insertion notes stored.</div>
                )}

                <h4 className="mt-5 text-sm font-semibold text-slate-900">Adaptation notes</h4>
                {adaptationNotes.length > 0 ? (
                  <ul className="mt-2 space-y-2">
                    {adaptationNotes.map((note) => (
                      <li key={note} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-7 text-slate-700">
                        {note}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="mt-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">No adaptation notes stored.</div>
                )}

                <h4 className="mt-5 text-sm font-semibold text-slate-900">Validation warnings</h4>
                {validationWarnings.length > 0 ? (
                  <ul className="mt-2 space-y-2">
                    {validationWarnings.map((warning) => (
                      <li key={warning} className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-7 text-amber-900">
                        {warning}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="mt-2 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
                    No validation warnings stored.
                  </div>
                )}

                <h4 className="mt-5 text-sm font-semibold text-slate-900">Scene seed notes</h4>
                {sceneSeedNotes.length > 0 ? (
                  <div className="mt-2 space-y-3">
                    {sceneSeedNotes.map((note) => (
                      <div key={`${note.sceneIndex}-${note.label}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-900">
                            Scene {note.sceneIndex}: {note.label}
                          </p>
                          <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-medium text-slate-600">
                            {note.mood || "mood not set"}
                          </span>
                        </div>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">{note.setting || "setting not set"}</p>
                        <p className="mt-3 text-sm leading-7 text-slate-700">{note.keyVisualAction}</p>
                        <p className="mt-3 text-xs leading-6 text-slate-500">Anchor: {note.excerptAnchor || "No excerpt anchor stored."}</p>
                        <p className="mt-2 text-xs leading-6 text-slate-500">
                          Characters: {note.featuredCharacters.length > 0 ? note.featuredCharacters.join(", ") : "No Buddybug cameo characters required"}
                        </p>
                        <p className="mt-2 text-xs leading-6 text-slate-500">{note.illustrationNotes || "No illustration notes stored."}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-2 rounded-2xl bg-slate-50 p-4 text-sm text-slate-600">No scene seed notes stored.</div>
                )}
              </div>

              <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-lg font-semibold text-slate-900">Editor notes</h3>
                <textarea
                  value={editorNotes}
                  onChange={(event) => setEditorNotes(event.target.value)}
                  rows={5}
                  className="mt-3 w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
                  placeholder="Leave approval notes, publishing checks, or cameo restraint reminders"
                />
                <button
                  type="button"
                  disabled={Boolean(working)}
                  onClick={() =>
                    void runAction("save-notes", async () => {
                      if (!token || !latestDraft) {
                        return;
                      }
                      await apiPatch(
                        `/classics/drafts/${latestDraft.id}`,
                        { editor_notes: editorNotes || null },
                        { token, timeoutMs: 60_000 },
                      );
                      setMessage("Editor notes saved.");
                      await loadPage(source.id);
                    })
                  }
                  className="mt-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
                >
                  {working === "save-notes" ? "Saving..." : "Save notes"}
                </button>
              </div>

              <div className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">Pages and preview</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      Generated page/scene data for the existing illustration and preview pipeline.
                    </p>
                  </div>
                  {bundle.preview_book ? (
                    <Link
                      href={`/reader/${bundle.preview_book.id}?preview=1`}
                      className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
                    >
                      Open preview
                    </Link>
                  ) : null}
                </div>
                <div className="mt-4 space-y-3">
                  {bundle.story_pages.map((page) => (
                    <div key={page.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-slate-900">Page {page.page_number}</p>
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-medium text-slate-600">
                          {page.image_status}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-slate-700">{page.scene_summary}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        {page.location} • {page.mood} • {page.characters_present || "No cameo characters"}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <EmptyState
              title="No Buddybug draft yet"
              description="Once the source is verified, create a Buddybug draft to start the editorial adaptation pipeline."
            />
          )}
        </div>
      </section>
    </div>
  );
}
