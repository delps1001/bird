from __future__ import annotations

import io
import logging
import queue
import threading
import time
import wave
from datetime import datetime, timedelta

from bird_listener.config import Config
from bird_listener.ports import (
    AudioSource,
    BirdAnalyzer,
    DetectionRepository,
    DisplayDriver,
    DisplayRenderer,
)
from bird_listener.ranking.service import rank_birds

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        config: Config,
        repository: DetectionRepository,
        renderer: DisplayRenderer,
        display: DisplayDriver,
        audio: AudioSource | None = None,
        analyzer: BirdAnalyzer | None = None,
    ) -> None:
        self._config = config
        self._audio = audio
        self._analyzer = analyzer
        self._repo = repository
        self._renderer = renderer
        self._display = display
        self._audio_queue: queue.Queue[tuple[bytes, int]] = queue.Queue(maxsize=2)
        self._stop = threading.Event()
        self._last_ranked_names: list[str] | None = None

    def run_once(self) -> None:
        """Execute one capture-analyze-render cycle (for testing)."""
        now = datetime.now()

        logger.info("Capturing audio...")
        wav_data, _sr = self._audio.capture()

        logger.info("Analyzing audio...")
        detections = self._analyzer.analyze(
            wav_data,
            lat=self._config.lat,
            lon=self._config.lon,
            date=now,
            min_conf=self._config.min_confidence,
        )

        for det in detections:
            self._repo.record_detection(det)
            logger.info("Detected: %s (%.0f%%)", det.common_name, det.confidence * 100)

        self._render_display(now)

    def run_loop(self) -> None:
        """Run continuously with overlapping capture and analysis.

        A background thread captures audio non-stop, feeding chunks into
        a queue. The main thread pulls chunks off and analyzes them, so
        there are no gaps in audio coverage.
        """
        logger.info(
            "Starting bird listener (capture=%ds, continuous)",
            self._config.capture_duration_sec,
        )
        self._stop.clear()

        capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        capture_thread.start()

        try:
            while not self._stop.is_set():
                try:
                    wav_data, _sr = self._audio_queue.get(timeout=1)
                except queue.Empty:
                    continue

                now = datetime.now()
                logger.info("Analyzing audio...")
                detections = self._analyzer.analyze(
                    wav_data,
                    lat=self._config.lat,
                    lon=self._config.lon,
                    date=now,
                    min_conf=self._config.min_confidence,
                )

                for det in detections:
                    self._repo.record_detection(det)
                    logger.info("Detected: %s (%.0f%%)", det.common_name, det.confidence * 100)

                self._render_display(now)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self._stop.set()

    def run_display_only(self, once: bool = False) -> None:
        """Poll the repository and re-render the display on an interval.

        No audio capture or analysis — just read from the DB and display.
        """
        logger.info(
            "Starting display-only mode (refresh every %ds)",
            self._config.loop_interval_sec,
        )
        self._stop.clear()

        try:
            while not self._stop.is_set():
                self._render_display(datetime.now())
                if once:
                    break
                self._stop.wait(timeout=self._config.loop_interval_sec)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self._stop.set()

    def _capture_loop(self) -> None:
        """Continuously capture audio and enqueue chunks."""
        while not self._stop.is_set():
            try:
                logger.info("Capturing audio...")
                wav_data, sr = self._audio.capture()

                # Audio diagnostics
                try:
                    buf = io.BytesIO(wav_data)
                    with wave.open(buf, "rb") as wf:
                        n_frames = wf.getnframes()
                        duration = n_frames / wf.getframerate()
                        raw = wf.readframes(n_frames)
                    import numpy as np
                    samples = np.frombuffer(raw, dtype="int16")
                    peak = int(np.max(np.abs(samples))) if len(samples) > 0 else 0
                    rms = int(np.sqrt(np.mean(samples.astype(float) ** 2))) if len(samples) > 0 else 0
                    logger.info(
                        "Audio chunk: %.1fs, %d samples, peak=%d, rms=%d (of 32768)",
                        duration, len(samples), peak, rms,
                    )
                except Exception as e:
                    logger.warning("Could not inspect audio: %s", e)

                try:
                    self._audio_queue.put_nowait((wav_data, sr))
                except queue.Full:
                    # Drop oldest if analysis can't keep up
                    try:
                        self._audio_queue.get_nowait()
                    except queue.Empty:
                        pass
                    self._audio_queue.put_nowait((wav_data, sr))
                    logger.warning("Analysis falling behind, dropped oldest audio chunk")
            except Exception:
                logger.exception("Error capturing audio")
                time.sleep(1)

    def _render_display(self, now: datetime) -> None:
        since = now - timedelta(hours=self._config.recent_window_hours)
        recent = self._repo.get_detections_since(since)
        lifetime = self._repo.get_lifetime_counts()
        first_seen = self._repo.get_first_detection_times()
        ranked = rank_birds(recent, lifetime, first_seen=first_seen, new_since=since)

        ranked_names = [b.common_name for b in ranked]
        if ranked_names == self._last_ranked_names:
            logger.info("Bird list unchanged, skipping display refresh")
            return
        self._last_ranked_names = ranked_names

        logger.info("Rendering display with %d species...", len(ranked))
        image = self._renderer.render(
            ranked,
            self._config.assets_dir,
            self._config.display_width,
            self._config.display_height,
        )
        self._display.show(image)
