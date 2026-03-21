"use client";

import { useState } from "react";

import type { SupportTicketDetailResponse, SupportTicketRead } from "@/lib/types";

export function SupportTicketDetail({
  detail,
  onUpdate,
  onAddNote,
  onResolve,
  onClose,
}: {
  detail: SupportTicketDetailResponse;
  onUpdate: (payload: { status?: string; priority?: string; assigned_to_user_id?: number }) => Promise<void>;
  onAddNote: (payload: { body: string; note_type?: string; is_internal?: boolean }) => Promise<void>;
  onResolve: () => Promise<void>;
  onClose: () => Promise<void>;
}) {
  const [statusValue, setStatusValue] = useState(detail.ticket.status);
  const [priority, setPriority] = useState(detail.ticket.priority);
  const [assignedToUserId, setAssignedToUserId] = useState(detail.ticket.assigned_to_user_id?.toString() || "");
  const [noteBody, setNoteBody] = useState("");
  const [saving, setSaving] = useState(false);
  const [noteSaving, setNoteSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpdate() {
    setSaving(true);
    setError(null);
    try {
      await onUpdate({
        status: statusValue,
        priority,
        assigned_to_user_id: assignedToUserId ? Number(assignedToUserId) : undefined,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update ticket");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddNote() {
    setNoteSaving(true);
    setError(null);
    try {
      await onAddNote({ body: noteBody });
      setNoteBody("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to add note");
    } finally {
      setNoteSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-xl font-semibold text-slate-900">{detail.ticket.subject}</h3>
            <p className="mt-1 text-sm text-slate-600">
              {detail.ticket.category} {detail.ticket.email ? `• ${detail.ticket.email}` : ""}
            </p>
          </div>
          <div className="flex gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{detail.ticket.status}</span>
            <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">{detail.ticket.priority}</span>
          </div>
        </div>
        <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-slate-700">{detail.ticket.message}</p>
      </section>

      <section className="grid gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Triage</h3>
        <div className="grid gap-3 sm:grid-cols-3">
          <select
            value={statusValue}
            onChange={(event) => setStatusValue(event.target.value)}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            {["open", "in_progress", "waiting_for_user", "resolved", "closed"].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select
            value={priority}
            onChange={(event) => setPriority(event.target.value)}
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          >
            {["low", "normal", "high", "urgent"].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <input
            value={assignedToUserId}
            onChange={(event) => setAssignedToUserId(event.target.value)}
            placeholder="Assign to user ID"
            className="rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
          />
        </div>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <div className="grid gap-3 sm:grid-cols-3">
          <button
            type="button"
            onClick={() => void handleUpdate()}
            disabled={saving}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900 disabled:opacity-60"
          >
            {saving ? "Saving..." : "Save triage changes"}
          </button>
          <button
            type="button"
            onClick={() => void onResolve()}
            className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
          >
            Resolve ticket
          </button>
          <button
            type="button"
            onClick={() => void onClose()}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-900"
          >
            Close ticket
          </button>
        </div>
      </section>

      <section className="space-y-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">Internal notes</h3>
        <textarea
          value={noteBody}
          onChange={(event) => setNoteBody(event.target.value)}
          rows={4}
          placeholder="Add internal note"
          className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900"
        />
        <button
          type="button"
          onClick={() => void handleAddNote()}
          disabled={noteSaving || !noteBody.trim()}
          className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {noteSaving ? "Adding..." : "Add internal note"}
        </button>
        <div className="grid gap-3">
          {detail.notes.map((note) => (
            <div key={note.id} className="rounded-2xl bg-slate-50 px-4 py-3 text-sm">
              <p className="font-medium text-slate-900">
                {note.note_type} {note.is_internal ? "• internal" : ""}
              </p>
              <p className="mt-2 whitespace-pre-wrap text-slate-700">{note.body}</p>
              <p className="mt-2 text-xs text-slate-500">{new Date(note.created_at).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
