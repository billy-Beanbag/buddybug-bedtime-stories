from __future__ import annotations

import io
import math
import struct
import wave


def estimate_tts_duration_seconds(text: str) -> int:
    word_count = max(1, len(text.split()))
    estimated = math.ceil(word_count / 2.6)
    return max(2, min(estimated, 12))


class LocalMockTTSAdapter:
    """Small local TTS placeholder that emits a simple WAV tone."""

    sample_rate = 16_000

    def generate_speech(self, text: str, voice_key: str, language: str) -> bytes:
        duration_seconds = estimate_tts_duration_seconds(text)
        frame_count = self.sample_rate * duration_seconds
        amplitude = 4_000
        frequency = 440 + (sum(ord(char) for char in f"{voice_key}:{language}") % 180)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            for frame_index in range(frame_count):
                value = int(amplitude * math.sin((2 * math.pi * frequency * frame_index) / self.sample_rate))
                wav_file.writeframesraw(struct.pack("<h", value))
        return buffer.getvalue()
