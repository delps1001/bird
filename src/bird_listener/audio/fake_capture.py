from __future__ import annotations

import io
import wave
from pathlib import Path


class FakeAudioSource:
    """Returns canned WAV data for development and testing."""

    def __init__(self, wav_path: Path | None = None, sample_rate: int = 48000) -> None:
        self._sample_rate = sample_rate
        if wav_path and wav_path.exists():
            self._wav_data = wav_path.read_bytes()
        else:
            # Generate silent WAV
            self._wav_data = self._silent_wav()

    def capture(self) -> tuple[bytes, int]:
        return self._wav_data, self._sample_rate

    def _silent_wav(self) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._sample_rate)
            # 3 seconds of silence
            wf.writeframes(b"\x00" * self._sample_rate * 2 * 3)
        return buf.getvalue()
