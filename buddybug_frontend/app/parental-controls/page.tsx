"use client";

import Link from "next/link";

import { ChildOverrideForm } from "@/components/ChildOverrideForm";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ParentalControlsForm } from "@/components/ParentalControlsForm";
import { useAuth } from "@/context/AuthContext";
import { useChildProfiles } from "@/context/ChildProfileContext";
import { useParentalControls } from "@/context/ParentalControlsContext";

export default function ParentalControlsPage() {
  const { isAuthenticated, token, isLoading } = useAuth();
  const { childProfiles } = useChildProfiles();
  const { parentSettings, isLoading: parentalLoading, refreshParentalControls, updateParentSettings } = useParentalControls();

  if (isLoading || parentalLoading) {
    return <LoadingState message="Loading parental controls..." />;
  }

  if (!isAuthenticated || !token) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Parental controls are available after login"
          description="Sign in to manage bedtime mode, autoplay, and content limits for your family."
        />
        <Link
          href="/login"
          className="block rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
        >
          Log in
        </Link>
      </div>
    );
  }

  if (!parentSettings) {
    return <EmptyState title="Unable to load parental controls" description="Try refreshing this page." />;
  }

  return (
    <div className="space-y-4">
      <ParentalControlsForm settings={parentSettings} onSave={updateParentSettings} />
      {childProfiles.length ? (
        <section className="space-y-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Child overrides</h2>
            <p className="mt-1 text-sm text-slate-600">Optional overrides for each child profile.</p>
          </div>
          {childProfiles.map((childProfile) => (
            <ChildOverrideForm
              key={childProfile.id}
              childProfile={childProfile}
              token={token}
              onUpdated={refreshParentalControls}
            />
          ))}
        </section>
      ) : null}
    </div>
  );
}
