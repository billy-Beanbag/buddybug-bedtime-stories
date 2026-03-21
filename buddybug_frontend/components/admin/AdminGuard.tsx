"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { useAuth } from "@/context/AuthContext";
import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";

export function AdminGuard({ children }: { children: ReactNode }) {
  const { isLoading, isAuthenticated, isAdmin } = useAuth();

  if (isLoading) {
    return <LoadingState message="Checking admin access..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <EmptyState title="Login required" description="Sign in with an admin account to access the internal dashboard." />
        <div className="mt-4">
          <Link
            href="/login"
            className={`inline-flex rounded-2xl px-4 py-3 font-medium ${ADMIN_PRIMARY_BUTTON}`}
          >
            Go to login
          </Link>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <EmptyState
          title="Access denied"
          description="Your account is signed in, but it does not have admin access."
        />
      </div>
    );
  }

  return <>{children}</>;
}
