"use client";

import Link from "next/link";

import { ReadAlongJoinForm } from "@/components/ReadAlongJoinForm";
import { ReadAlongSessionBadge } from "@/components/ReadAlongSessionBadge";
import type { ReadAlongDetailResponse } from "@/lib/types";

export function ReadAlongPanel({
  isAuthenticated,
  isOnline,
  bookId,
  activeSession,
  loading = false,
  actionLoading = null,
  error = null,
  onCreate,
  onJoin,
  onEnd,
}: {
  isAuthenticated: boolean;
  isOnline: boolean;
  bookId: number;
  activeSession: ReadAlongDetailResponse | null;
  loading?: boolean;
  actionLoading?: "create" | "join" | "end" | null;
  error?: string | null;
  onCreate: () => Promise<void> | void;
  onJoin: (joinCode: string) => Promise<void> | void;
  onEnd: () => Promise<void> | void;
}) {
  const activeForThisBook = activeSession && activeSession.session.book_id === bookId ? activeSession : null;

  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div>
        <h3 className="text-xl font-semibold text-slate-900">Read Together</h3>
        <p className="mt-1 text-sm text-slate-600">
          Create a private session for this story and keep page turns in sync across your family’s logged-in devices.
        </p>
      </div>

      {!isAuthenticated ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600">
          Sign in to create or join a private read-along session.
        </div>
      ) : null}

      {isAuthenticated && !isOnline ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Read-along is online-only for now. Reconnect to create or join a shared session.
        </div>
      ) : null}

      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}

      {activeForThisBook ? (
        <div className="space-y-3">
          <ReadAlongSessionBadge detail={activeForThisBook} />
          <div className="flex flex-wrap gap-3">
            <Link
              href="/read-along"
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
            >
              Open all sessions
            </Link>
            <button
              type="button"
              onClick={() => void onEnd()}
              disabled={!isOnline || actionLoading === "end"}
              className="rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm font-medium text-rose-700 disabled:opacity-60"
            >
              {actionLoading === "end" ? "Ending..." : "End session"}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <button
            type="button"
            onClick={() => void onCreate()}
            disabled={!isAuthenticated || !isOnline || loading || actionLoading === "create"}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
          >
            {actionLoading === "create" ? "Creating session..." : "Start reading together"}
          </button>
          <div className="rounded-2xl bg-slate-50 px-4 py-4">
            <p className="text-sm font-medium text-slate-900">Join from another device</p>
            <p className="mt-1 text-sm text-slate-600">
              Enter a private code from this account’s other device to follow the shared page.
            </p>
            <div className="mt-3">
              <ReadAlongJoinForm
                disabled={!isAuthenticated || !isOnline || loading}
                loading={actionLoading === "join"}
                onJoin={onJoin}
                buttonLabel="Join on this device"
              />
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
