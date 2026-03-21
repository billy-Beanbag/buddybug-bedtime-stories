"use client";

interface FamilyDigestChildCardProps {
  childName: string;
  storiesOpened: number;
  storiesCompleted: number;
  narrationUses: number;
  achievementsEarned: number;
  currentStreakDays: number;
  summaryText: string | null;
  highlighted?: boolean;
}

export function FamilyDigestChildCard({
  childName,
  storiesOpened,
  storiesCompleted,
  narrationUses,
  achievementsEarned,
  currentStreakDays,
  summaryText,
  highlighted = false,
}: FamilyDigestChildCardProps) {
  return (
    <article
      className={`space-y-3 rounded-[2rem] border p-5 shadow-sm ${
        highlighted ? "border-indigo-200 bg-indigo-50/70" : "border-white/70 bg-white/85"
      }`}
    >
      <div>
        <h3 className="text-xl font-semibold text-slate-900">{childName}</h3>
        <p className="mt-1 text-sm leading-6 text-slate-600">
          {summaryText || "A gentle Buddybug snapshot is ready for this reading week."}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-2xl bg-white/80 px-4 py-3">
          <p className="text-slate-500">Opened</p>
          <p className="mt-1 text-lg font-semibold text-slate-900">{storiesOpened}</p>
        </div>
        <div className="rounded-2xl bg-white/80 px-4 py-3">
          <p className="text-slate-500">Completed</p>
          <p className="mt-1 text-lg font-semibold text-slate-900">{storiesCompleted}</p>
        </div>
        <div className="rounded-2xl bg-white/80 px-4 py-3">
          <p className="text-slate-500">Narration</p>
          <p className="mt-1 text-lg font-semibold text-slate-900">{narrationUses}</p>
        </div>
        <div className="rounded-2xl bg-white/80 px-4 py-3">
          <p className="text-slate-500">Achievements</p>
          <p className="mt-1 text-lg font-semibold text-slate-900">{achievementsEarned}</p>
        </div>
      </div>

      <div className="rounded-2xl bg-white/80 px-4 py-3 text-sm text-slate-700">
        Current streak: <span className="font-semibold text-slate-900">{currentStreakDays} day(s)</span>
      </div>
    </article>
  );
}
