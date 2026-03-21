"use client";

export function ReadingStreakCard({
  currentStreak,
  longestStreak,
  scopeLabel,
}: {
  currentStreak: number;
  longestStreak: number;
  scopeLabel: string;
}) {
  return (
    <section className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
      <div>
        <h3 className="text-xl font-semibold text-slate-900">Reading rhythm</h3>
        <p className="mt-1 text-sm text-slate-600">A calm view of {scopeLabel.toLowerCase()} reading consistency.</p>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-slate-50 px-4 py-4">
          <p className="text-sm text-slate-500">Current streak</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{currentStreak}</p>
          <p className="mt-1 text-xs text-slate-500">day{currentStreak === 1 ? "" : "s"}</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-4">
          <p className="text-sm text-slate-500">Longest streak</p>
          <p className="mt-2 text-3xl font-semibold text-slate-900">{longestStreak}</p>
          <p className="mt-1 text-xs text-slate-500">day{longestStreak === 1 ? "" : "s"}</p>
        </div>
      </div>
    </section>
  );
}
