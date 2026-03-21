"use client";

import Link from "next/link";

import { ChildProfileCard } from "@/components/ChildProfileCard";
import { CreateChildProfileForm } from "@/components/CreateChildProfileForm";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";

export default function ChildrenPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { childProfiles, selectedChildProfile, setSelectedChildProfile, refreshChildProfiles, isLoading } =
    useChildProfiles();

  if (authLoading || isLoading) {
    return <LoadingState message="Loading child profiles..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Sign in to manage child profiles"
          description="Child profiles are available for authenticated family accounts."
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
    <section className="space-y-4">
      <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(135deg,#111827_0%,#1e1b4b_42%,#312e81_74%,#4338ca_100%)] p-5 text-white shadow-[0_24px_60px_rgba(30,41,59,0.18)]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.12),transparent_30%),radial-gradient(circle_at_bottom_right,rgba(251,191,36,0.16),transparent_26%)]" />
        <div className="relative">
        <h2 className="text-2xl font-semibold text-white">Child profiles</h2>
        <p className="mt-1 text-sm text-indigo-100">
          Pick who the app is reading for so progress and recommendations stay child-aware.
        </p>
        {childProfiles.length ? (
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/bedtime-pack"
              className="inline-flex rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white"
            >
              Open bedtime pack
            </Link>
            <Link
              href="/reading-plans"
              className="inline-flex rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white"
            >
              Reading plans
            </Link>
            <Link
              href="/family-digest"
              className="inline-flex rounded-2xl border border-white/15 bg-white/10 px-4 py-3 text-sm font-medium text-white"
            >
              Family digest
            </Link>
          </div>
        ) : null}
        </div>
      </div>

      <CreateChildProfileForm token={token} onCreated={refreshChildProfiles} />

      {childProfiles.length ? (
        <div className="grid gap-3">
          {childProfiles.map((profile) => (
            <ChildProfileCard
              key={profile.id}
              profile={profile}
              selected={selectedChildProfile?.id === profile.id}
              onSelect={setSelectedChildProfile}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          title="No child profiles yet"
          description="Create your first child profile to personalize reading, progress, and recommendations."
        />
      )}
    </section>
  );
}
