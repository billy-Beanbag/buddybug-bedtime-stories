"use client";

const bandClassNames: Record<string, string> = {
  healthy: "bg-emerald-100 text-emerald-700",
  watch: "bg-amber-100 text-amber-700",
  at_risk: "bg-orange-100 text-orange-700",
  churned: "bg-rose-100 text-rose-700",
};

export function HealthBandBadge({ band }: { band: string }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium ${bandClassNames[band] || "bg-slate-100 text-slate-700"}`}>
      {band.replaceAll("_", " ")}
    </span>
  );
}
