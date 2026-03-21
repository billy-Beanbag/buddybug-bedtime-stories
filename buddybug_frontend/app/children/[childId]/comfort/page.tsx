"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ChildComfortProfileForm, type ChildComfortFormValues } from "@/components/ChildComfortProfileForm";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { apiGet, apiPatch } from "@/lib/api";
import type { ChildComfortProfileRead, ChildProfileRead } from "@/lib/types";

function toPayload(values: ChildComfortFormValues) {
  return {
    favorite_characters_csv: values.favorite_characters_csv.trim() || null,
    favorite_moods_csv: values.favorite_moods_csv.trim() || null,
    favorite_story_types_csv: values.favorite_story_types_csv.trim() || null,
    avoid_tags_csv: values.avoid_tags_csv.trim() || null,
    preferred_language: values.preferred_language || null,
    prefer_narration: values.prefer_narration,
    prefer_shorter_stories: values.prefer_shorter_stories,
    extra_calm_mode: values.extra_calm_mode,
    bedtime_notes: values.bedtime_notes.trim() || null,
  };
}

export default function ChildComfortPage() {
  const params = useParams<{ childId: string }>();
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { childProfiles, isLoading: childrenLoading } = useChildProfiles();
  const [childProfile, setChildProfile] = useState<ChildProfileRead | null>(null);
  const [profile, setProfile] = useState<ChildComfortProfileRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const profileFromContext = childProfiles.find((item) => String(item.id) === params.childId) || null;
    if (profileFromContext) {
      setChildProfile(profileFromContext);
    }
  }, [childProfiles, params.childId]);

  useEffect(() => {
    if (authLoading || childrenLoading) {
      return;
    }
    if (!isAuthenticated || !token || !params.childId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    void Promise.all([
      apiGet<ChildProfileRead>(`/child-profiles/${params.childId}`, { token }),
      apiGet<ChildComfortProfileRead>(`/child-comfort/${params.childId}`, { token }),
    ])
      .then(([childResponse, comfortResponse]) => {
        setChildProfile(childResponse);
        setProfile(comfortResponse);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load comfort preferences"))
      .finally(() => setLoading(false));
  }, [authLoading, childrenLoading, isAuthenticated, params.childId, token]);

  async function handleSave(values: ChildComfortFormValues) {
    if (!token || !params.childId) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const response = await apiPatch<ChildComfortProfileRead>(`/child-comfort/${params.childId}`, toPayload(values), { token });
      setProfile(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to update comfort preferences";
      setError(message);
      throw err;
    } finally {
      setSaving(false);
    }
  }

  if (authLoading || childrenLoading || loading) {
    return <LoadingState message="Loading comfort preferences..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to manage comfort preferences"
          description="Child comfort profiles are available for authenticated family accounts."
        />
        <div className="grid grid-cols-2 gap-3">
          <Link
            href="/login"
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Log in
          </Link>
          <Link href="/register" className="rounded-2xl bg-slate-900 px-4 py-3 text-center font-medium text-white">
            Create account
          </Link>
        </div>
      </div>
    );
  }

  if (!childProfile || !profile) {
    return (
      <EmptyState
        title="Comfort preferences unavailable"
        description={error || "This child profile could not be loaded."}
      />
    );
  }

  return (
    <div className="space-y-4">
      {error ? <EmptyState title="Could not update comfort preferences" description={error} /> : null}

      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">{childProfile.display_name}</h2>
        <p className="mt-1 text-sm text-slate-600">
          These preferences offer gentle guidance for recommendations, bedtime packs, and reading plans.
        </p>
      </section>

      <ChildComfortProfileForm childProfile={childProfile} profile={profile} submitting={saving} onSave={handleSave} />
    </div>
  );
}
