"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { VisualReferenceEditor } from "@/components/admin/VisualReferenceEditor";
import { VisualReferenceTable } from "@/components/admin/VisualReferenceTable";
import { useAuth } from "@/context/AuthContext";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { VisualReferenceAssetRead, VisualReferenceImportResponse } from "@/lib/types";

interface CharacterOption {
  id: number;
  name: string;
}

export default function AdminVisualReferencesPage() {
  const { token, isEditor } = useAuth();
  const [assets, setAssets] = useState<VisualReferenceAssetRead[]>([]);
  const [characters, setCharacters] = useState<CharacterOption[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<VisualReferenceAssetRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [targetType, setTargetType] = useState("");
  const [targetId, setTargetId] = useState("");
  const [referenceType, setReferenceType] = useState("");

  async function loadAssets(nextTargetType = targetType, nextTargetId = targetId, nextReferenceType = referenceType) {
    if (!token) {
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await apiGet<VisualReferenceAssetRead[]>("/admin/visual-references", {
        token,
        query: {
          target_type: nextTargetType || undefined,
          target_id: nextTargetType && nextTargetId ? Number(nextTargetId) : undefined,
          reference_type: nextReferenceType || undefined,
          limit: 100,
        },
      });
      setAssets(response);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Unable to load visual references");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (token) {
      void loadAssets();
      void (async () => {
        try {
          const response = await apiGet<CharacterOption[]>("/characters", { token });
          setCharacters(response);
        } catch {
          setCharacters([]);
        }
      })();
    }
  }, [token]);

  if (!isEditor) {
    return <EmptyState title="Editor access required" description="Only editors and admins can manage visual reference assets." />;
  }

  if (loading) {
    return <LoadingState message="Loading visual references..." />;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Visual references</h1>
        <p className="mt-2 text-sm text-slate-600">
          Track reusable illustration references, style boards, and prompt notes so recurring characters and worlds stay consistent.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <select
            value={referenceType}
            onChange={(event) => setReferenceType(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All reference types</option>
            <option value="character_sheet">character_sheet</option>
            <option value="style_reference">style_reference</option>
            <option value="cover_reference">cover_reference</option>
            <option value="scene_reference">scene_reference</option>
          </select>
          <select
            value={targetType}
            onChange={(event) => setTargetType(event.target.value)}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
          >
            <option value="">All targets</option>
            <option value="character">character</option>
            <option value="content_lane">content_lane</option>
            <option value="editorial_project">editorial_project</option>
            <option value="book">book</option>
            <option value="story_draft">story_draft</option>
          </select>
          <input
            type="number"
            min={1}
            value={targetId}
            onChange={(event) => setTargetId(event.target.value)}
            disabled={!targetType}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 disabled:bg-slate-50"
            placeholder="Target ID"
          />
          <button
            type="button"
            onClick={() => void loadAssets(targetType, targetId, referenceType)}
            className={`rounded-2xl px-4 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Apply filters
          </button>
          <button
            type="button"
            disabled={importing}
            onClick={async () => {
              if (!token) {
                return;
              }
              setImporting(true);
              setStatusMessage(null);
              setErrorMessage(null);
              try {
                const response = await apiPost<VisualReferenceImportResponse>(
                  "/admin/visual-references/import-character-bible",
                  undefined,
                  { token },
                );
                setStatusMessage(
                  `Character bible import finished. Created ${response.created}, updated ${response.updated}, scanned ${response.scanned}.`,
                );
                await loadAssets();
              } catch (err) {
                setErrorMessage(err instanceof Error ? err.message : "Unable to import character bible references");
              } finally {
                setImporting(false);
              }
            }}
            className="rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
          >
            {importing ? "Importing..." : "Import Character Bible"}
          </button>
        </div>
        {characters.length ? (
          <div className="mt-5 rounded-2xl bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-900">Character asset base helpers</p>
            <p className="mt-1 text-sm text-slate-600">
              Use `character_sheet` assets targeted to these canonical characters to lock faces, collars, and proportions.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {characters.map((character) => (
                <button
                  key={character.id}
                  type="button"
                  onClick={() => {
                    setTargetType("character");
                    setTargetId(String(character.id));
                    setSelectedAsset(null);
                  }}
                  className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700"
                >
                  {character.name} #{character.id}
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      {statusMessage ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</div>
      ) : null}
      {errorMessage ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{errorMessage}</div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <VisualReferenceEditor
          asset={selectedAsset}
          characterOptions={characters}
          submitting={saving}
          onClear={() => setSelectedAsset(null)}
          onSubmit={async (payload, assetId) => {
            if (!token) {
              return;
            }
            setSaving(true);
            setStatusMessage(null);
            setErrorMessage(null);
            try {
              if (assetId) {
                await apiPatch(`/admin/visual-references/${assetId}`, payload, { token });
                setStatusMessage("Updated visual reference asset.");
              } else {
                await apiPost("/admin/visual-references", payload, { token });
                setStatusMessage("Created visual reference asset.");
              }
              setSelectedAsset(null);
              await loadAssets();
            } catch (err) {
              setErrorMessage(err instanceof Error ? err.message : "Unable to save visual reference asset");
            } finally {
              setSaving(false);
            }
          }}
        />

        {assets.length ? (
          <VisualReferenceTable
            assets={assets}
            deletingId={deletingId}
            onEdit={(asset) => setSelectedAsset(asset)}
            onDelete={async (asset) => {
              if (!token) {
                return;
              }
              setDeletingId(asset.id);
              setStatusMessage(null);
              setErrorMessage(null);
              try {
                await apiDelete(`/admin/visual-references/${asset.id}`, { token });
                setSelectedAsset((current) => (current?.id === asset.id ? null : current));
                setStatusMessage(`Deleted "${asset.name}".`);
                await loadAssets();
              } catch (err) {
                setErrorMessage(err instanceof Error ? err.message : "Unable to delete visual reference asset");
              } finally {
                setDeletingId(null);
              }
            }}
          />
        ) : (
          <EmptyState
            title="No visual references yet"
            description="Create the first reference asset to capture a stable character sheet, style guide, cover look, or scene reference."
          />
        )}
      </div>
    </div>
  );
}
