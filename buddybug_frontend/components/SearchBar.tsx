"use client";

export function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = "Search stories by title or theme",
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  placeholder?: string;
}) {
  return (
    <div className="flex gap-2">
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            onSubmit?.();
          }
        }}
        placeholder={placeholder}
        className="flex-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900"
      />
      <button
        type="button"
        onClick={() => onSubmit?.()}
        className="rounded-2xl bg-slate-900 px-4 py-3 text-sm font-medium text-white"
      >
        Search
      </button>
    </div>
  );
}
