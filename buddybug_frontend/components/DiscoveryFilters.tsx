"use client";

export interface DiscoveryFilterState {
  ageBand: string;
  language: string;
  bedtimeSafe: boolean;
}

export function DiscoveryFilters({
  filters,
  onChange,
  allowedAgeOptions = ["", "3-7", "8-12"],
}: {
  filters: DiscoveryFilterState;
  onChange: (next: DiscoveryFilterState) => void;
  allowedAgeOptions?: string[];
}) {
  return (
    <div className="grid gap-3 rounded-3xl border border-white/70 bg-white/80 p-4 shadow-sm sm:grid-cols-3">
      <select
        value={filters.ageBand}
        onChange={(event) => onChange({ ...filters, ageBand: event.target.value })}
        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
      >
        {allowedAgeOptions.map((option) => (
          <option key={option || "all"} value={option}>
            {option || "All ages"}
          </option>
        ))}
      </select>
      <input
        value={filters.language}
        onChange={(event) => onChange({ ...filters, language: event.target.value })}
        placeholder="Language (en, es, fr)"
        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
      />
      <label className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900">
        <span>Bedtime-safe only</span>
        <input
          type="checkbox"
          checked={filters.bedtimeSafe}
          onChange={(event) => onChange({ ...filters, bedtimeSafe: event.target.checked })}
        />
      </label>
    </div>
  );
}
