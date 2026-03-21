"use client";

import Link from "next/link";

import type { ClassroomSetRead } from "@/lib/types";

export function ClassroomSetList({ sets }: { sets: ClassroomSetRead[] }) {
  return (
    <div className="grid gap-4">
      {sets.map((classroomSet) => (
        <Link
          key={classroomSet.id}
          href={`/educator/classroom-sets/${classroomSet.id}`}
          className="rounded-3xl border border-white/70 bg-white/85 p-5 shadow-sm transition hover:-translate-y-0.5"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">{classroomSet.title}</h2>
              <p className="mt-1 text-sm text-slate-600">
                {classroomSet.description || "Teacher-managed classroom reading set."}
              </p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                classroomSet.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
              }`}
            >
              {classroomSet.is_active ? "Active" : "Inactive"}
            </span>
          </div>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
            {classroomSet.age_band ? <span className="rounded-full bg-slate-100 px-3 py-1">{classroomSet.age_band}</span> : null}
            {classroomSet.language ? <span className="rounded-full bg-slate-100 px-3 py-1">{classroomSet.language.toUpperCase()}</span> : null}
          </div>
        </Link>
      ))}
    </div>
  );
}
