"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { PremiumUpgradeCard } from "@/components/PremiumUpgradeCard";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet, apiPost } from "@/lib/api";
import type { StorySuggestionListResponse, StorySuggestionRead } from "@/lib/types";

type SuggestionFormState = {
  childProfileId: string;
  ageBand: string;
  title: string;
  brief: string;
  desiredOutcome: string;
  inspirationNotes: string;
  avoidNotes: string;
  allowReferenceUse: boolean;
};

const EMPTY_FORM: SuggestionFormState = {
  childProfileId: "",
  ageBand: "3-7",
  title: "",
  brief: "",
  desiredOutcome: "",
  inspirationNotes: "",
  avoidNotes: "",
  allowReferenceUse: true,
};

function formatStatusLabel(status: string) {
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export default function StorySuggestionsPage() {
  const router = useRouter();
  const { hasPremiumAccess, isAuthenticated, token } = useAuth();
  const { childProfiles, selectedChildProfile, isLoading: childProfilesLoading } = useChildProfiles();
  const [items, setItems] = useState<StorySuggestionRead[]>([]);
  const [form, setForm] = useState<SuggestionFormState>(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const childProfileOptions = useMemo(() => childProfiles.filter((profile) => profile.is_active), [childProfiles]);

  useEffect(() => {
    if (!selectedChildProfile) {
      return;
    }
    setForm((current) => ({
      ...current,
      childProfileId: current.childProfileId || String(selectedChildProfile.id),
      ageBand: current.ageBand || selectedChildProfile.age_band,
    }));
  }, [selectedChildProfile]);

  useEffect(() => {
    async function loadSuggestions() {
      if (!isAuthenticated || !token) {
        setItems([]);
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const response = await apiGet<StorySuggestionListResponse>("/story-suggestions/me", { token });
        setItems(response.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load story suggestions");
      } finally {
        setLoading(false);
      }
    }

    void loadSuggestions();
  }, [isAuthenticated, token]);

  async function handleSubmit() {
    if (!token) {
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const created = await apiPost<StorySuggestionRead>(
        "/story-suggestions",
        {
          child_profile_id: form.childProfileId ? Number(form.childProfileId) : null,
          age_band: form.ageBand,
          title: form.title.trim() || null,
          brief: form.brief.trim(),
          desired_outcome: form.desiredOutcome.trim() || null,
          inspiration_notes: form.inspirationNotes.trim() || null,
          avoid_notes: form.avoidNotes.trim() || null,
          allow_reference_use: form.allowReferenceUse,
        },
        { token },
      );
      setItems((current) => [created, ...current]);
      setForm({
        ...EMPTY_FORM,
        childProfileId: selectedChildProfile ? String(selectedChildProfile.id) : "",
        ageBand: selectedChildProfile?.age_band || "3-7",
      });
      setMessage("Suggestion saved. Editorial can now review it and reuse it as a future reference if approved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save story suggestion");
    } finally {
      setSaving(false);
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to suggest stories"
          description="Story suggestions are linked to your Buddybug account so editorial can review them alongside your family context."
        />
        <div className="flex flex-wrap gap-3">
          <Link
            href="/register/free?source=story_suggestions"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
          >
            Create account
          </Link>
          <Link
            href="/upgrade"
            className="rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-3 text-sm font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)]"
          >
            View Premium
          </Link>
        </div>
      </div>
    );
  }

  if (!hasPremiumAccess) {
    return (
      <div className="space-y-4">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Story suggestions</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Premium parents can share a quick scenario, mood, or lesson they want Buddybug to explore. Approved ideas can
            feed the editorial memory for future stories without retraining the model itself.
          </p>
        </section>
        <PremiumUpgradeCard onUpgrade={() => router.push("/register/premium?source=story_suggestions")} />
      </div>
    );
  }

  if (loading || childProfilesLoading) {
    return <LoadingState message="Loading story suggestions..." />;
  }

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Suggest a future story</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Share a scenario, tone, or lesson you would love to see. Buddybug can use approved suggestions as editorial
          guidance for future ideas and prompts.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="font-medium">Child profile</span>
            <select
              value={form.childProfileId}
              onChange={(event) => {
                const nextId = event.target.value;
                const nextProfile = childProfileOptions.find((profile) => String(profile.id) === nextId);
                setForm((current) => ({
                  ...current,
                  childProfileId: nextId,
                  ageBand: nextProfile?.age_band || current.ageBand,
                }));
              }}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            >
              <option value="">General family idea</option>
              {childProfileOptions.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.display_name} • {profile.age_band}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="font-medium">Age band</span>
            <select
              value={form.ageBand}
              onChange={(event) => setForm((current) => ({ ...current, ageBand: event.target.value }))}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            >
              <option value="3-7">3-7</option>
              <option value="8-12">8-12</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm text-slate-700 md:col-span-2">
            <span className="font-medium">Working title</span>
            <input
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              placeholder="The lost moon ribbon"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <label className="grid gap-1 text-sm text-slate-700 md:col-span-2">
            <span className="font-medium">Scenario or outline</span>
            <textarea
              value={form.brief}
              onChange={(event) => setForm((current) => ({ ...current, brief: event.target.value }))}
              rows={6}
              placeholder="Daphne loses the ribbon from her bedtime lantern and has to retrace the calm places she visited that day to find it."
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="font-medium">What should the story deliver?</span>
            <textarea
              value={form.desiredOutcome}
              onChange={(event) => setForm((current) => ({ ...current, desiredOutcome: event.target.value }))}
              rows={4}
              placeholder="A reassuring ending that helps with first-night nerves."
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="font-medium">Details to include</span>
            <textarea
              value={form.inspirationNotes}
              onChange={(event) => setForm((current) => ({ ...current, inspirationNotes: event.target.value }))}
              rows={4}
              placeholder="Lantern light, moon garden, gentle treasure-hunt feel."
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            />
          </label>
          <label className="grid gap-1 text-sm text-slate-700 md:col-span-2">
            <span className="font-medium">Things to avoid</span>
            <textarea
              value={form.avoidNotes}
              onChange={(event) => setForm((current) => ({ ...current, avoidNotes: event.target.value }))}
              rows={3}
              placeholder="Too much peril, loud conflict, or a sleepy ending if this should stay more playful."
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            />
          </label>
        </div>
        <label className="mt-4 flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.allowReferenceUse}
            onChange={(event) => setForm((current) => ({ ...current, allowReferenceUse: event.target.checked }))}
            className="mt-1 h-4 w-4 rounded border-slate-300 text-indigo-600"
          />
          <span>
            If editorial approves this, Buddybug can reuse it as a style and prompt reference for future stories. This
            shapes the editorial memory, not the underlying model weights.
          </span>
        </label>
        {message ? <p className="mt-4 text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={saving || !form.brief.trim()}
            onClick={() => void handleSubmit()}
            className="rounded-2xl bg-[linear-gradient(135deg,#4338ca_0%,#5b21b6_100%)] px-4 py-3 text-sm font-medium text-white shadow-[0_16px_36px_rgba(79,70,229,0.18)] disabled:opacity-60"
          >
            {saving ? "Saving suggestion..." : "Save suggestion"}
          </button>
          <Link
            href="/library"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
          >
            Back to library
          </Link>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">Suggestion history</h3>
            <p className="mt-1 text-sm text-slate-600">
              Track which ideas are still waiting, under review, or approved as reusable references.
            </p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700">{items.length} total</span>
        </div>
        {!items.length ? (
          <div className="mt-4">
            <EmptyState
              title="No suggestions yet"
              description="Once you save a story idea here, it will appear in this history list for editorial review."
            />
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {items.map((item) => (
              <article key={item.id} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h4 className="text-base font-semibold text-slate-900">{item.title || "Untitled suggestion"}</h4>
                    <p className="mt-1 text-sm text-slate-500">
                      {item.age_band} • {item.language.toUpperCase()} • {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-white px-3 py-2 text-sm font-medium text-slate-700">
                      {formatStatusLabel(item.status)}
                    </span>
                    {item.approved_as_reference ? (
                      <span className="rounded-full bg-emerald-100 px-3 py-2 text-sm font-medium text-emerald-800">
                        Reusable reference
                      </span>
                    ) : null}
                  </div>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-700">{item.brief}</p>
                {item.desired_outcome ? (
                  <p className="mt-3 text-sm text-slate-600">
                    <span className="font-medium text-slate-900">Goal:</span> {item.desired_outcome}
                  </p>
                ) : null}
                {item.editorial_notes ? (
                  <div className="mt-3 rounded-2xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-900">
                    <span className="font-medium">Editorial notes:</span> {item.editorial_notes}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
