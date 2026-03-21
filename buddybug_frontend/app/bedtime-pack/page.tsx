"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BedtimePackCard } from "@/components/BedtimePackCard";
import { BedtimePackItemCard } from "@/components/BedtimePackItemCard";
import { EmptyState } from "@/components/EmptyState";
import { GenerateBedtimePackButton } from "@/components/GenerateBedtimePackButton";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type {
  BedtimePackDetailResponse,
  BedtimePackGenerateResponse,
  BedtimePackItemRead,
  BedtimePackRead,
} from "@/lib/types";

export default function BedtimePackPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { childProfiles, selectedChildProfile, isLoading: childrenLoading } = useChildProfiles();
  const [detail, setDetail] = useState<BedtimePackDetailResponse | null>(null);
  const [history, setHistory] = useState<BedtimePackRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionKey, setActionKey] = useState<string | null>(null);

  async function loadPack(currentToken: string) {
    const [latestResponse, historyResponse] = await Promise.all([
      apiGet<BedtimePackDetailResponse>("/bedtime-packs/me/latest", {
        token: currentToken,
        query: { child_profile_id: selectedChildProfile?.id },
      }),
      apiGet<BedtimePackRead[]>("/bedtime-packs/me", {
        token: currentToken,
        query: { child_profile_id: selectedChildProfile?.id, limit: 12 },
      }),
    ]);
    setDetail(latestResponse);
    setHistory(historyResponse);
  }

  useEffect(() => {
    if (authLoading || childrenLoading) {
      return;
    }
    if (!isAuthenticated || !token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    void loadPack(token)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load bedtime pack"))
      .finally(() => setLoading(false));
  }, [authLoading, childrenLoading, isAuthenticated, selectedChildProfile?.id, token]);

  async function handleGenerated(response: BedtimePackGenerateResponse) {
    setDetail({ pack: response.pack, items: response.items });
    if (token) {
      await loadPack(token);
    }
  }

  async function updateItem(item: BedtimePackItemRead, completionStatus: string) {
    if (!token || !detail) {
      return;
    }
    const key = `${item.id}:${completionStatus}`;
    setActionKey(key);
    setError(null);
    try {
      await apiPatch<BedtimePackItemRead>(
        `/bedtime-packs/me/${detail.pack.id}/items/${item.id}`,
        { completion_status: completionStatus },
        { token },
      );
      await loadPack(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update bedtime pack item");
    } finally {
      setActionKey(null);
    }
  }

  async function handleArchive() {
    if (!token || !detail) {
      return;
    }
    setActionKey("archive");
    setError(null);
    try {
      await apiPost(`/bedtime-packs/me/${detail.pack.id}/archive`, undefined, { token });
      await loadPack(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to archive bedtime pack");
    } finally {
      setActionKey(null);
    }
  }

  if (authLoading || childrenLoading || loading) {
    return <LoadingState message="Loading bedtime pack..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to see bedtime packs"
          description="Bedtime packs are available for signed-in Buddybug family accounts."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white"
          >
            Create account
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
        <div className="relative">
        <h2 className="text-2xl font-semibold text-white">Bedtime pack</h2>
        <p className="mt-2 text-sm leading-6 text-indigo-100">
          A calm multi-story session for tonight, tailored to your child profile, language, and bedtime preferences.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <GenerateBedtimePackButton
            token={token}
            childProfileId={selectedChildProfile?.id || null}
            onGenerated={handleGenerated}
          />
          {detail ? (
            <button
              type="button"
              onClick={() => void handleArchive()}
              disabled={actionKey === "archive"}
              className="rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
            >
              {actionKey === "archive" ? "Archiving..." : "Archive pack"}
            </button>
          ) : null}
        </div>
        </div>
      </section>

      {error ? <EmptyState title="Unable to load bedtime pack" description={error} /> : null}

      {detail ? (
        <BedtimePackCard pack={detail.pack} childProfiles={childProfiles} />
      ) : (
        <EmptyState
          title="No bedtime pack yet"
          description="Generate tonight's pack to line up a gentle bedtime reading routine."
        />
      )}

      <section className="space-y-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Tonight's stories</h3>
          <p className="mt-1 text-sm text-slate-600">
            Open them in order or simply use the pack as a calm guide for the evening.
          </p>
        </div>
        <div className="grid gap-3">
          {detail?.items.map((item, index) => (
            <BedtimePackItemCard
              key={item.id}
              item={item}
              isCurrent={index === 0}
              loadingAction={
                actionKey === `${item.id}:complete` ? "complete" : actionKey === `${item.id}:open` ? "open" : null
              }
              onOpen={(openedItem) => updateItem(openedItem, "opened")}
              onComplete={(completedItem) => updateItem(completedItem, "completed")}
            />
          )) || (
            <div className="rounded-[2rem] border border-dashed border-slate-300 bg-slate-50 px-5 py-4 text-sm text-slate-600">
              Generate a pack to see tonight's story sequence.
            </div>
          )}
        </div>
      </section>

      <section className="relative space-y-3 overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#0f172a_0%,#1d2457_45%,#302a6f_78%,#47377a_100%)] p-6 text-white shadow-[0_24px_60px_rgba(30,41,59,0.16)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,244,196,0.18),transparent_28%),radial-gradient(circle_at_18%_18%,rgba(129,140,248,0.2),transparent_30%)]" />
        <div className="relative">
        <div>
          <h3 className="text-xl font-semibold text-white">Recent packs</h3>
          <p className="mt-1 text-sm text-indigo-100">Short-lived bedtime sessions stay here for gentle reuse when helpful.</p>
        </div>
        {history.length ? (
          <div className="grid gap-3">
            {history.map((pack) => (
              <div key={pack.id} className="rounded-2xl border border-white/10 bg-white/10 px-4 py-3">
                <p className="font-medium text-white">{pack.title}</p>
                <p className="mt-1 text-sm text-indigo-200">
                  {pack.active_date || "No date"} • {pack.status} • {pack.pack_type}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-indigo-100">Recent bedtime packs will appear here after the first one is generated.</p>
        )}
        </div>
      </section>
    </div>
  );
}
