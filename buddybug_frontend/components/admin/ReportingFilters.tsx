"use client";

export interface ReportingFilterState {
  days: string;
  startDate: string;
  endDate: string;
}

export function ReportingFilters({
  value,
  onChange,
}: {
  value: ReportingFilterState;
  onChange: (next: ReportingFilterState) => void;
}) {
  return (
    <div className="grid gap-3 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-[180px_1fr_1fr]">
      <select
        value={value.days}
        onChange={(event) => onChange({ ...value, days: event.target.value })}
        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
      >
        <option value="7">Last 7 days</option>
        <option value="30">Last 30 days</option>
        <option value="90">Last 90 days</option>
        <option value="">Custom range</option>
      </select>
      <input
        type="date"
        value={value.startDate}
        onChange={(event) => onChange({ ...value, startDate: event.target.value, days: "" })}
        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
      />
      <input
        type="date"
        value={value.endDate}
        onChange={(event) => onChange({ ...value, endDate: event.target.value, days: "" })}
        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
      />
    </div>
  );
}
