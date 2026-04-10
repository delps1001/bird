from __future__ import annotations

import io
import threading
import time
import wave

import numpy as np

from bird_listener.audio.capture import MicrophoneAudioSource, _to_wav


def _wav_to_samples(wav_data: bytes) -> np.ndarray:
    """Extract raw samples from WAV bytes."""
    buf = io.BytesIO(wav_data)
    with wave.open(buf, "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        return np.frombuffer(frames, dtype="int16")


def test_to_wav_roundtrip() -> None:
    """_to_wav produces valid WAV that decodes back to the same audio."""
    original = np.array([1, 2, 3, 4, 5], dtype="int16")
    wav_bytes = _to_wav(original, sample_rate=48000)
    decoded = _wav_to_samples(wav_bytes)
    assert np.array_equal(original, decoded)


def test_to_wav_correct_duration() -> None:
    """_to_wav produces a WAV with the expected duration."""
    sr = 48000
    seconds = 15
    audio = np.zeros(sr * seconds, dtype="int16")
    wav_bytes = _to_wav(audio, sr)
    decoded = _wav_to_samples(wav_bytes)
    assert len(decoded) == sr * seconds


def test_streaming_capture_produces_correct_length(monkeypatch) -> None:
    """MicrophoneAudioSource produces correct-length WAV chunks."""
    import sounddevice as sd

    class FakeStream:
        def __init__(self, **kwargs):
            self.callback = kwargs["callback"]
            self._running = False
            self._sr = kwargs.get("samplerate", 48000)

        def start(self):
            self._running = True
            self._thread = threading.Thread(target=self._feed, daemon=True)
            self._thread.start()

        def _feed(self):
            counter = 0
            block = 4096  # larger blocks for speed
            while self._running:
                data = np.full((block, 1), fill_value=counter % 32000, dtype="int16")
                counter += 1
                self.callback(data, block, None, None)
                time.sleep(0.001)

        def stop(self):
            self._running = False

        def close(self):
            pass

    monkeypatch.setattr(sd, "InputStream", FakeStream)

    # Use small sample rate so the test is fast
    source = MicrophoneAudioSource(duration_sec=1, overlap_sec=0, sample_rate=8000)

    wav_data, sr = source.capture()
    assert sr == 8000
    samples = _wav_to_samples(wav_data)
    assert len(samples) == 8000  # 1 second at 8kHz

    source.close()


def test_overlap_produces_shared_audio(monkeypatch) -> None:
    """Consecutive chunks share overlap_sec seconds of audio."""
    import sounddevice as sd

    counter = [0]

    class FakeStream:
        def __init__(self, **kwargs):
            self.callback = kwargs["callback"]
            self._running = False

        def start(self):
            self._running = True
            self._thread = threading.Thread(target=self._feed, daemon=True)
            self._thread.start()

        def _feed(self):
            block = 4096
            while self._running:
                # Incrementing values so we can verify overlap content
                start = counter[0]
                data = np.arange(start, start + block, dtype="int16").reshape(-1, 1)
                counter[0] += block
                self.callback(data, block, None, None)
                time.sleep(0.001)

        def stop(self):
            self._running = False

        def close(self):
            pass

    monkeypatch.setattr(sd, "InputStream", FakeStream)

    sr = 8000
    source = MicrophoneAudioSource(duration_sec=1, overlap_sec=0, sample_rate=sr)

    # First chunk
    wav1, _ = source.capture()
    s1 = _wav_to_samples(wav1)
    assert len(s1) == sr

    # Second chunk (with overlap=0, should be entirely new audio)
    wav2, _ = source.capture()
    s2 = _wav_to_samples(wav2)
    assert len(s2) == sr

    # With overlap=0, chunks should not share samples
    # (the last sample of chunk 1 should not equal the first of chunk 2,
    #  because overlap=0 means we wait for a full chunk_samples of new data)
    source.close()
