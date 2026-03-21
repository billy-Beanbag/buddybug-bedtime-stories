"use client";

import type { NarrationVoiceRead } from "@/lib/types";

interface VoiceSelectorProps {
  voices: NarrationVoiceRead[];
  selectedVoiceKey: string | null;
  onChange: (voiceKey: string) => void;
}

export function VoiceSelector({ voices, selectedVoiceKey, onChange }: VoiceSelectorProps) {
  if (!voices.length) {
    return null;
  }

  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-slate-700">Voice</span>
      <select
        value={selectedVoiceKey ?? voices[0].key}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none"
      >
        {voices.map((voice) => (
          <option key={voice.key} value={voice.key}>
            {voice.display_name}
            {voice.is_premium ? " (Premium)" : ""}
          </option>
        ))}
      </select>
      {selectedVoiceKey ? (
        <p className="mt-2 text-xs text-slate-500">
          {voices.find((voice) => voice.key === selectedVoiceKey)?.description || "Choose a narration voice."}
        </p>
      ) : null}
    </label>
  );
}
