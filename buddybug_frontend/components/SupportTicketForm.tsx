"use client";

import { useState } from "react";

const SUPPORT_CATEGORIES = [
  "general_support",
  "billing_issue",
  "bug_report",
  "content_concern",
  "feature_request",
  "parental_controls_question",
] as const;

export function SupportTicketForm({
  isAuthenticated,
  initialEmail = "",
  onSubmit,
}: {
  isAuthenticated: boolean;
  initialEmail?: string;
  onSubmit: (payload: {
    category: string;
    subject: string;
    message: string;
    email?: string;
    child_profile_id?: number;
    related_book_id?: number;
    source: string;
  }) => Promise<void>;
}) {
  const [category, setCategory] = useState<(typeof SUPPORT_CATEGORIES)[number]>("general_support");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState(initialEmail);
  const [relatedBookId, setRelatedBookId] = useState("");
  const [childProfileId, setChildProfileId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await onSubmit({
        category,
        subject,
        message,
        email: isAuthenticated ? undefined : email || undefined,
        related_book_id: relatedBookId ? Number(relatedBookId) : undefined,
        child_profile_id: childProfileId ? Number(childProfileId) : undefined,
        source: isAuthenticated ? "app" : "web",
      });
      setSubject("");
      setMessage("");
      setRelatedBookId("");
      setChildProfileId("");
      if (!isAuthenticated) {
        setEmail(initialEmail);
      }
      setSuccess("Your support request has been sent.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send support request");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Contact support</h3>
        <p className="mt-1 text-sm text-slate-600">Tell the Buddybug team what is going wrong or what would help most.</p>
      </div>
      {!isAuthenticated ? (
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          placeholder="Your email"
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          required
        />
      ) : null}
      <select
        value={category}
        onChange={(event) => setCategory(event.target.value as (typeof SUPPORT_CATEGORIES)[number])}
        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
      >
        {SUPPORT_CATEGORIES.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <input
        value={subject}
        onChange={(event) => setSubject(event.target.value)}
        placeholder="Subject"
        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        required
      />
      <textarea
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        placeholder="How can we help?"
        rows={6}
        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        required
      />
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          value={relatedBookId}
          onChange={(event) => setRelatedBookId(event.target.value)}
          placeholder="Related book ID (optional)"
          className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
        {isAuthenticated ? (
          <input
            value={childProfileId}
            onChange={(event) => setChildProfileId(event.target.value)}
            placeholder="Child profile ID (optional)"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        ) : null}
      </div>
      {success ? <p className="text-sm text-emerald-700">{success}</p> : null}
      {error ? <p className="text-sm text-rose-600">{error}</p> : null}
      <button
        type="submit"
        disabled={saving}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
      >
        {saving ? "Sending..." : "Send support request"}
      </button>
    </form>
  );
}
