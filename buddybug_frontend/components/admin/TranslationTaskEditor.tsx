"use client";

import { useEffect, useState } from "react";

import { ADMIN_PRIMARY_BUTTON } from "@/lib/admin-styles";
import type { TranslationTaskDetailResponse } from "@/lib/types";

export function TranslationTaskEditor({
  item,
  saving,
  onCreate,
  onUpdate,
}: {
  item: TranslationTaskDetailResponse | null;
  saving: boolean;
  onCreate: (payload: Record<string, unknown>) => Promise<void>;
  onUpdate: (taskId: number, payload: Record<string, unknown>) => Promise<void>;
}) {
  const [bookId, setBookId] = useState("");
  const [language, setLanguage] = useState("es");
  const [status, setStatus] = useState("not_started");
  const [assignedToUserId, setAssignedToUserId] = useState("");
  const [sourceVersionLabel, setSourceVersionLabel] = useState("");
  const [notes, setNotes] = useState("");
  const [dueAt, setDueAt] = useState("");

  useEffect(() => {
    setBookId(item ? String(item.book_id) : "");
    setLanguage(item?.target_language || "es");
    setStatus(item?.task?.status || "not_started");
    setAssignedToUserId(item?.task?.assigned_to_user_id ? String(item.task.assigned_to_user_id) : "");
    setSourceVersionLabel(item?.task?.source_version_label || "");
    setNotes(item?.task?.notes || "");
    setDueAt(item?.task?.due_at ? item.task.due_at.slice(0, 16) : "");
  }, [item]);

  return (
    <section className="rounded-3xl border border-white/70 bg-white/85 p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">{item?.task ? "Edit translation task" : "Create translation task"}</h2>
        <p className="mt-1 text-sm text-slate-600">
          Track assignment, status, and notes for a single book/language translation workflow.
        </p>
      </div>

      <div className="mt-4 grid gap-4">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Book ID</span>
          <input
            type="number"
            min={1}
            value={bookId}
            onChange={(event) => setBookId(event.target.value)}
            disabled={Boolean(item?.task)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 disabled:bg-slate-50"
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Target language</span>
            <input
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              disabled={Boolean(item?.task)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 disabled:bg-slate-50"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Status</span>
            <select
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            >
              <option value="not_started">not_started</option>
              <option value="in_progress">in_progress</option>
              <option value="in_review">in_review</option>
              <option value="completed">completed</option>
              <option value="blocked">blocked</option>
            </select>
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Assigned user ID</span>
            <input
              type="number"
              min={1}
              value={assignedToUserId}
              onChange={(event) => setAssignedToUserId(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
              placeholder="Optional"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-700">Due at</span>
            <input
              type="datetime-local"
              value={dueAt}
              onChange={(event) => setDueAt(event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            />
          </label>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Source version label</span>
          <input
            value={sourceVersionLabel}
            onChange={(event) => setSourceVersionLabel(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="v1, approved-2026-03-16, or similar"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Notes</span>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={5}
            className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
            placeholder="Internal translation notes, blockers, or QA context"
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={saving || !bookId || !language}
          onClick={() => {
            const payload = {
              book_id: Number(bookId),
              language,
              status,
              assigned_to_user_id: assignedToUserId ? Number(assignedToUserId) : null,
              source_version_label: sourceVersionLabel || null,
              notes: notes || null,
              due_at: dueAt ? new Date(dueAt).toISOString() : null,
            };
            if (item?.task) {
              void onUpdate(item.task.id, {
                status: payload.status,
                assigned_to_user_id: payload.assigned_to_user_id,
                source_version_label: payload.source_version_label,
                notes: payload.notes,
                due_at: payload.due_at,
              });
            } else {
              void onCreate(payload);
            }
          }}
          className={`rounded-2xl px-5 py-3 text-sm font-medium ${ADMIN_PRIMARY_BUTTON}`}
        >
          {saving ? "Saving..." : item?.task ? "Save task" : "Create task"}
        </button>
      </div>
    </section>
  );
}
