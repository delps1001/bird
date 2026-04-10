from __future__ import annotations

import io
import threading
import wave

import numpy as np
import sounddevice as sd


class MicrophoneAudioSource:
    """Captures audio continuously using a persistent stream and ring buffer.

    The audio device stays open the entire time, so there are no gaps
    from device open/close cycles. Each call to capture() returns
    `duration_sec` of audio. Consecutive chunks overlap by `overlap_sec`
    so bird calls at chunk boundaries are fully covered.
    """

    def __init__(
        self,
        duration_sec: int = 15,
        overlap_sec: int = 3,
        sample_rate: int = 48000,
    ) -> None:
        self._duration = duration_sec
        self._overlap = overlap_sec
        self._sample_rate = sample_rate
        self._chunk_samples = duration_sec * sample_rate
        self._new_samples = (duration_sec - overlap_sec) * sample_rate

        # Ring buffer: double the chunk size so we can always read a full chunk
        buf_size = self._chunk_samples * 2
        self._buffer = np.zeros(buf_size, dtype="int16")
        self._write_pos = 0
        self._lock = threading.Lock()

        # Tracks how many new samples have arrived since last capture() returned
        self._new_since_last = 0
        self._first_capture = True
        self._has_enough = threading.Event()

        # Persistent audio stream — opens once, stays open
        self._stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocksize=1024,
            callback=self._audio_callback,
        )
        self._stream.start()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Called by PortAudio on its own thread with new audio data."""
        samples = indata[:, 0]  # shape (frames,) mono
        n = len(samples)

        with self._lock:
            buf_len = len(self._buffer)
            end = self._write_pos + n
            if end <= buf_len:
                self._buffer[self._write_pos:end] = samples
            else:
                first = buf_len - self._write_pos
                self._buffer[self._write_pos:] = samples[:first]
                self._buffer[:n - first] = samples[first:]
            self._write_pos = end % buf_len
            self._new_since_last += n

            # How many new samples do we need?
            needed = self._chunk_samples if self._first_capture else self._new_samples
            if self._new_since_last >= needed:
                self._has_enough.set()

    def capture(self) -> tuple[bytes, int]:
        """Block until enough new audio has arrived, then return a chunk."""
        self._has_enough.wait()

        with self._lock:
            self._has_enough.clear()
            self._first_capture = False
            self._new_since_last = 0

            # Read the last chunk_samples from the ring buffer
            buf_len = len(self._buffer)
            end = self._write_pos
            start = (end - self._chunk_samples) % buf_len

            if start < end:
                audio = self._buffer[start:end].copy()
            else:
                audio = np.concatenate([
                    self._buffer[start:],
                    self._buffer[:end],
                ])

        return _to_wav(audio, self._sample_rate), self._sample_rate

    def close(self) -> None:
        self._stream.stop()
        self._stream.close()


def _to_wav(audio: np.ndarray, sample_rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()
