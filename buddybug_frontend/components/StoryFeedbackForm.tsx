"use client";

import { useEffect, useMemo, useState } from "react";

import { apiGet, apiPatch, apiPost, ApiError } from "@/lib/api";
import type {
  FeedbackSummaryResponse,
  UserStoryFeedbackRead,
} from "@/lib/types";

interface StoryFeedbackFormProps {
  bookId: number;
  token: string | null;
  canSubmit: boolean;
  childProfileId: number | null;
  completed: boolean;
}

type LikedValue = "liked" | "not_liked" | "unset";

function feedbackToLikedValue(feedback: UserStoryFeedbackRead | null): LikedValue {
  if (!feedback || feedback.liked === null) {
    return "unset";
  }
  return feedback.liked ? "liked" : "not_liked";
}

export function StoryFeedbackForm({
  bookId,
  token,
  canSubmit,
  childProfileId,
  completed,
}: StoryFeedbackFormProps) {
  const [feedback, setFeedback] = useState<UserStoryFeedbackRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [likedValue, setLikedValue] = useState<LikedValue>("unset");
  const [rating, setRating] = useState<number | null>(null);
  const [notes, setNotes] = useState("");
  const [replayed, setReplayed] = useState(false);

  useEffect(() => {
    if (!token || !canSubmit) {
      setLoading(false);
      return;
    }

    async function loadFeedback() {
      try {
        const existing = await apiGet<UserStoryFeedbackRead>(`/feedback/me/books/${bookId}`, {
          token,
          query: { child_profile_id: childProfileId ?? undefined },
        });
        setFeedback(existing);
        setLikedValue(feedbackToLikedValue(existing));
        setRating(existing.rating);
        setNotes(existing.feedback_notes || "");
        setReplayed(existing.replayed);
      } catch (err) {
        if (!(err instanceof ApiError) || err.status !== 404) {
          setError(err instanceof Error ? err.message : "Unable to load feedback");
        }
      } finally {
        setLoading(false);
      }
    }

    void loadFeedback();
  }, [bookId, canSubmit, childProfileId, token]);

  const liked = useMemo(() => {
    if (likedValue === "unset") {
      return null;
    }
    return likedValue === "liked";
  }, [likedValue]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setSubmitting(true);
    setSuccessMessage(null);
    setError(null);

    const payload = {
      child_profile_id: childProfileId,
      liked,
      rating,
      completed,
      replayed,
      feedback_notes: notes || null,
    };

    try {
      const result = feedback
        ? await apiPatch<FeedbackSummaryResponse>(`/feedback/me/books/${bookId}`, payload, { token })
        : await apiPost<FeedbackSummaryResponse>(`/feedback/me/books/${bookId}`, payload, { token });

      setFeedback(result.feedback);
      setSuccessMessage("Feedback saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save feedback");
    } finally {
      setSubmitting(false);
    }
  }

  if (!canSubmit) {
    return (
      <section className="rounded-[2rem] border border-dashed border-slate-300 bg-white/70 p-4 text-sm text-slate-600 shadow-sm">
        Log in to rate this story.
      </section>
    );
  }

  if (loading) {
    return (
      <section className="rounded-[2rem] border border-white/70 bg-white/90 p-4 text-sm text-slate-600 shadow-sm">
        Loading feedback form...
      </section>
    );
  }

  return (
    <section className="space-y-4 rounded-[2rem] border border-white/70 bg-white/90 p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Rate this story</h3>
        <p className="mt-1 text-sm text-slate-600">Tell Buddybug what felt most enjoyable about this book.</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <p className="mb-2 text-sm font-medium text-slate-700">Did you enjoy it?</p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setLikedValue("liked")}
              className={`rounded-2xl px-3 py-3 text-sm font-medium ${
                likedValue === "liked" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
              }`}
            >
              Yes
            </button>
            <button
              type="button"
              onClick={() => setLikedValue("not_liked")}
              className={`rounded-2xl px-3 py-3 text-sm font-medium ${
                likedValue === "not_liked" ? "bg-rose-100 text-rose-800" : "bg-slate-100 text-slate-700"
              }`}
            >
              No
            </button>
            <button
              type="button"
              onClick={() => setLikedValue("unset")}
              className={`rounded-2xl px-3 py-3 text-sm font-medium ${
                likedValue === "unset" ? "bg-indigo-100 text-indigo-800" : "bg-slate-100 text-slate-700"
              }`}
            >
              Skip
            </button>
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-slate-700">Rating</p>
          <div className="grid grid-cols-5 gap-2">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setRating(value)}
                className={`rounded-2xl px-3 py-3 text-sm font-semibold ${
                  rating === value ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                }`}
              >
                {value}
              </button>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={replayed}
            onChange={(event) => setReplayed(event.target.checked)}
            className="h-4 w-4 rounded border-slate-300"
          />
          I would like to replay this story again
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Short note</span>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={3}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
            placeholder="Optional thoughts about this bedtime story"
          />
        </label>

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        {successMessage ? <p className="text-sm text-emerald-700">{successMessage}</p> : null}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-2xl bg-slate-900 px-4 py-3 font-medium text-white disabled:opacity-60"
        >
          {submitting ? "Saving..." : feedback ? "Update feedback" : "Submit feedback"}
        </button>
      </form>
    </section>
  );
}
