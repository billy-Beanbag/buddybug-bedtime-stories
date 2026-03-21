"use client";

interface ComfortPreferenceChipsProps {
  label: string;
  description?: string;
  options: string[];
  selected: string[];
  disabled?: boolean;
  onChange: (values: string[]) => void;
}

export function ComfortPreferenceChips({
  label,
  description,
  options,
  selected,
  disabled = false,
  onChange,
}: ComfortPreferenceChipsProps) {
  function toggleValue(value: string) {
    if (disabled) {
      return;
    }
    const normalizedValue = value.toLowerCase();
    if (selected.includes(normalizedValue)) {
      onChange(selected.filter((item) => item !== normalizedValue));
      return;
    }
    onChange([...selected, normalizedValue]);
  }

  return (
    <div className="space-y-3 rounded-[1.75rem] bg-slate-50 px-4 py-4">
      <div>
        <h3 className="text-sm font-medium text-slate-900">{label}</h3>
        {description ? <p className="mt-1 text-sm text-slate-600">{description}</p> : null}
      </div>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const normalizedOption = option.toLowerCase();
          const isSelected = selected.includes(normalizedOption);
          return (
            <button
              key={option}
              type="button"
              disabled={disabled}
              onClick={() => toggleValue(option)}
              className={`rounded-full px-3 py-2 text-sm font-medium transition ${
                isSelected
                  ? "bg-slate-900 text-white"
                  : "border border-slate-200 bg-white text-slate-700 hover:border-slate-300"
              } disabled:opacity-60`}
            >
              {option}
            </button>
          );
        })}
      </div>
    </div>
  );
}
