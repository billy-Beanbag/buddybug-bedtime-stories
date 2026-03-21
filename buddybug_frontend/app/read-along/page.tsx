"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { ReadAlongJoinForm } from "@/components/ReadAlongJoinForm";
import { useAuth } from "@/context/AuthContext";
import { useConnectivity } from "@/context/ConnectivityContext";
import { apiGet, apiPost } from "@/lib/api";
import type { ReadAlongJoinResponse, ReadAlongSessionRead } from "@/lib/types";

function buildReaderHref(session: ReadAlongSessionRead) {
  return `/reader/${session.book_id}?readAlongSessionId=${session.id}`;
}

export default function ReadAlongPage() {
  const { isAuthenticated, isLoading: authLoading, token } = useAuth();
  const { isOnline } = useConnectivity();
  const [sessions, setSessions] = useState<ReadAlongSessionRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [joinError, setJoinError] = useState<string | null>(null);
  const [joining, setJoining] = useState(false);
  const [endingSessionId, setEndingSessionId] = useState<number | null>(null);
  const [lastJoinedSession, setLastJoinedSession] = useState<ReadAlongSessionRead | null>(null);

  useEffect(() => {
    if (authLoading) {
      return;
    }
    if (!isAuthenticated || !token) {
      setSessions([]);
      setLoading(false);
      return;
    }
    if (!isOnline) {
      setLoading(false);
      return;
    }

    async function loadSessions() {
      setLoading(true);
      setError(null);
      try {
        const response = await apiGet<ReadAlongSessionRead[]>("/read-along/me", { token, query: { limit: 20 } });
        setSessions(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unable to load read-along sessions");
      } finally {
        setLoading(false);
      }
    }

    void loadSessions();
  }, [authLoading, isAuthenticated, isOnline, token]);

  async function handleJoin(joinCode: string) {
    if (!token || !isOnline) {
      return;
    }
    setJoining(true);
    setJoinError(null);
    try {
      const response = await apiPost<ReadAlongJoinResponse>("/read-along/join", { join_code: joinCode }, { token });
      setLastJoinedSession(response.session);
      setSessions((current) => {
        const withoutDuplicate = current.filter((item) => item.id !== response.session.id);
        return [response.session, ...withoutDuplicate];
      });
    } catch (err) {
      setJoinError(err instanceof Error ? err.message : "Unable to join read-along session");
    } finally {
      setJoining(false);
    }
  }

  async function handleEndSession(sessionId: number) {
    if (!token || !isOnline) {
      return;
    }
    setEndingSessionId(sessionId);
    try {
      const endedSession = await apiPost<ReadAlongSessionRead>(`/read-along/sessions/${sessionId}/end`, undefined, { token });
      setSessions((current) => current.map((item) => (item.id === endedSession.id ? endedSession : item)));
      if (lastJoinedSession?.id === endedSession.id) {
        setLastJoinedSession(endedSession);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to end read-along session");
    } finally {
      setEndingSessionId(null);
    }
  }

  if (authLoading || loading) {
    return <LoadingState message="Loading shared reading sessions..." />;
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Read-along is for signed-in families"
          description="Sign in to create private shared reading sessions and continue together across devices."
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
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-center font-medium text-slate-900"
          >
            Create account
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <h2 className="text-2xl font-semibold text-slate-900">Read Along</h2>
        <p className="mt-2 text-sm text-slate-600">
          Keep a story in sync across your family’s own logged-in devices with a private join code and simple polling.
        </p>
        {!isOnline ? (
          <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Read-along needs a live connection right now. Your saved stories still work offline, but shared sessions do
            not sync until you’re back online.
          </div>
        ) : null}
      </section>

      <section className="rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-sm">
        <h3 className="text-xl font-semibold text-slate-900">Join with a code</h3>
        <p className="mt-1 text-sm text-slate-600">Use the six-character code from another device on this same account.</p>
        <div className="mt-4">
          <ReadAlongJoinForm disabled={!isOnline} loading={joining} onJoin={handleJoin} />
        </div>
        {joinError ? <p className="mt-3 text-sm text-rose-600">{joinError}</p> : null}
        {lastJoinedSession ? (
          <Link
            href={buildReaderHref(lastJoinedSession)}
            className="mt-4 inline-flex rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
          >
            Open joined story
          </Link>
        ) : null}
      </section>

      {error ? <EmptyState title="Unable to load read-along sessions" description={error} /> : null}

      <section className="space-y-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Active and recent sessions</h3>
          <p className="mt-1 text-sm text-slate-600">Reopen a shared story or end a session when story time is done.</p>
        </div>

        {!sessions.length ? (
          <EmptyState
            title="No read-along sessions yet"
            description="Start a session from any reader screen, then re-open it here on another device."
          />
        ) : (
          <div className="grid gap-3">
            {sessions.map((session) => (
              <article
                key={session.id}
                className="rounded-3xl border border-white/70 bg-white/85 p-5 shadow-sm"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
                      <span className="rounded-full bg-indigo-50 px-2 py-1 font-medium text-indigo-700">Code {session.join_code}</span>
                      <span className="capitalize">{session.status}</span>
                      <span>Page {session.current_page_number}</span>
                      <span className="capitalize">{session.playback_state.replace("_", " ")}</span>
                    </div>
                    <p className="text-sm text-slate-600">
                      Story #{session.book_id}
                      {session.child_profile_id ? ` • Child profile ${session.child_profile_id}` : ""}
                    </p>
                    <p className="text-xs text-slate-500">
                      Updated {new Date(session.updated_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Link
                      href={buildReaderHref(session)}
                      className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
                    >
                      Open story
                    </Link>
                    {session.status === "active" ? (
                      <button
                        type="button"
                        onClick={() => void handleEndSession(session.id)}
                        disabled={!isOnline || endingSessionId === session.id}
                        className="rounded-2xl border border-rose-200 bg-white px-4 py-3 text-sm font-medium text-rose-700 disabled:opacity-60"
                      >
                        {endingSessionId === session.id ? "Ending..." : "End session"}
                      </button>
                    ) : null}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
