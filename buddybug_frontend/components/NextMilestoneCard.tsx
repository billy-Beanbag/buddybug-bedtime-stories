"use client";

export function NextMilestoneCard({
  milestoneTitle,
  scopeLabel,
}: {
  milestoneTitle: string | null;
  scopeLabel: string;
}) {
  return (
    <section className="rounded-[2rem] border border-indigo-100 bg-indigo-50/80 p-5 shadow-sm">
      <h3 className="text-xl font-semibold text-slate-900">Next gentle milestone</h3>
      <p className="mt-1 text-sm text-slate-600">
        Buddybug keeps this light and family-friendly for {scopeLabel.toLowerCase()}.
      </p>
      <div className="mt-4 rounded-2xl bg-white/80 px-4 py-4">
        <p className="text-lg font-semibold text-slate-900">{milestoneTitle || "Enjoy the stories already earned"}</p>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Small reading moments matter. There is no leaderboard here, just a warm nudge toward steady story time.
        </p>
      </div>
    </section>
  );
}
