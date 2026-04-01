from __future__ import annotations

import io
import logging
import math
import struct
import wave
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status

from app.config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_BASE_URL,
    ELEVENLABS_MODEL_ID,
    ELEVENLABS_OUTPUT_FORMAT,
    ELEVENLABS_VOICE_IDS_BY_KEY,
    ELEVENLABS_VOICE_SETTINGS_BY_KEY,
    NARRATION_TTS_PROVIDER,
    NARRATION_TTS_REQUIRE_LIVE,
    NARRATION_TTS_TIMEOUT_SECONDS,
)
from app.models import NarrationVoice

logger = logging.getLogger(__name__)


def estimate_tts_duration_seconds(text: str) -> int:
    word_count = max(1, len(text.split()))
    estimated = math.ceil(word_count / 2.6)
    return max(2, min(estimated, 12))


@dataclass(frozen=True)
class SpeechSynthesisResult:
    audio_bytes: bytes
    duration_seconds: int
    file_extension: str
    provider: str
    provider_audio_id: str | None = None


class LocalMockTTSAdapter:
    """Small local TTS placeholder that emits a simple WAV tone."""

    sample_rate = 16_000

    def can_generate(self, _voice: NarrationVoice) -> bool:
        return True

    def generate_speech(self, *, text: str, voice: NarrationVoice, language: str) -> SpeechSynthesisResult:
        duration_seconds = estimate_tts_duration_seconds(text)
        frame_count = self.sample_rate * duration_seconds
        amplitude = 4_000
        frequency = 440 + (sum(ord(char) for char in f"{voice.key}:{language}") % 180)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            for frame_index in range(frame_count):
                value = int(amplitude * math.sin((2 * math.pi * frequency * frame_index) / self.sample_rate))
                wav_file.writeframesraw(struct.pack("<h", value))
        return SpeechSynthesisResult(
            audio_bytes=buffer.getvalue(),
            duration_seconds=duration_seconds,
            file_extension="wav",
            provider="mock",
        )


class ElevenLabsTTSAdapter:
    def __init__(self) -> None:
        self.api_key = ELEVENLABS_API_KEY
        self.base_url = ELEVENLABS_BASE_URL.rstrip("/")
        self.model_id = ELEVENLABS_MODEL_ID
        self.output_format = ELEVENLABS_OUTPUT_FORMAT
        self.timeout_seconds = NARRATION_TTS_TIMEOUT_SECONDS
        self.voice_ids_by_key = {
            str(key): str(value)
            for key, value in ELEVENLABS_VOICE_IDS_BY_KEY.items()
            if str(key).strip() and str(value).strip()
        }
        self.voice_settings_by_key = {
            str(key): value
            for key, value in ELEVENLABS_VOICE_SETTINGS_BY_KEY.items()
            if str(key).strip() and isinstance(value, dict)
        }

    def can_generate(self, voice: NarrationVoice) -> bool:
        return bool(self.api_key and self.voice_ids_by_key.get(voice.key))

    def generate_speech(self, *, text: str, voice: NarrationVoice, language: str) -> SpeechSynthesisResult:
        voice_id = self.voice_ids_by_key.get(voice.key)
        if not self.api_key or not voice_id:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ElevenLabs is not configured for narration voice '{voice.key}'",
            )

        payload: dict[str, object] = {"text": text, "model_id": self.model_id}
        voice_settings = self.voice_settings_by_key.get(voice.key)
        if voice_settings:
            payload["voice_settings"] = voice_settings

        response = httpx.post(
            f"{self.base_url}/text-to-speech/{voice_id}",
            params={"output_format": self.output_format},
            headers={
                "xi-api-key": self.api_key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.exception("ElevenLabs narration request failed for voice %s", voice.key)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Live narration generation failed",
            ) from exc

        history_item_id = response.headers.get("history-item-id")
        return SpeechSynthesisResult(
            audio_bytes=response.content,
            duration_seconds=estimate_tts_duration_seconds(text),
            file_extension=_extension_for_output_format(self.output_format),
            provider="elevenlabs",
            provider_audio_id=history_item_id,
        )


class ConfigurableTTSAdapter:
    def __init__(self) -> None:
        self.provider = (NARRATION_TTS_PROVIDER or "auto").strip().lower()
        self.require_live = NARRATION_TTS_REQUIRE_LIVE
        self.mock = LocalMockTTSAdapter()
        self.elevenlabs = ElevenLabsTTSAdapter()

    def generate_speech(self, *, text: str, voice: NarrationVoice, language: str) -> SpeechSynthesisResult:
        if self.provider == "mock":
            return self.mock.generate_speech(text=text, voice=voice, language=language)

        if self.elevenlabs.can_generate(voice):
            return self.elevenlabs.generate_speech(text=text, voice=voice, language=language)

        if self.provider == "elevenlabs" or self.require_live:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No live narration provider is configured for voice '{voice.key}'",
            )

        logger.warning("Falling back to mock narration for voice %s in %s", voice.key, language)
        return self.mock.generate_speech(text=text, voice=voice, language=language)

    def preferred_file_extension(self, voice: NarrationVoice) -> str:
        if self.provider != "mock" and self.elevenlabs.can_generate(voice):
            return _extension_for_output_format(self.elevenlabs.output_format)
        return "wav"


def _extension_for_output_format(output_format: str) -> str:
    lower_value = output_format.strip().lower()
    if lower_value.startswith("pcm_"):
        return "pcm"
    if lower_value.startswith("ulaw_"):
        return "ulaw"
    return "mp3"


def build_tts_adapter() -> ConfigurableTTSAdapter:
    return ConfigurableTTSAdapter()
