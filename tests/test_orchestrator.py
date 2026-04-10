from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

from bird_listener.config import Config
from bird_listener.display.file_driver import FileDisplayDriver
from bird_listener.display.renderer import PillowRenderer
from bird_listener.orchestrator import Orchestrator
from bird_listener.persistence.models import Detection
from bird_listener.persistence.repository import SQLiteDetectionRepository


class FakeAnalyzer:
    """Returns predetermined detections."""

    def __init__(self, detections: list[Detection]) -> None:
        self._detections = detections
        self.call_count = 0

    def analyze(
        self,
        wav_data: bytes,
        lat: float,
        lon: float,
        date: datetime,
        min_conf: float,
    ) -> list[Detection]:
        self.call_count += 1
        return self._detections


class SlowFakeAnalyzer(FakeAnalyzer):
    """Simulates slow analysis to test overlap behavior."""

    def __init__(self, detections: list[Detection], delay: float = 0.1) -> None:
        super().__init__(detections)
        self._delay = delay

    def analyze(self, wav_data, lat, lon, date, min_conf):
        time.sleep(self._delay)
        return super().analyze(wav_data, lat, lon, date, min_conf)


class CountingFakeAudio:
    """Tracks how many times capture() is called."""

    def __init__(self) -> None:
        self.call_count = 0

    def capture(self) -> tuple[bytes, int]:
        self.call_count += 1
        time.sleep(0.05)  # simulate short capture
        return b"fake-wav", 48000


ASSETS_DIR = Path(__file__).parent.parent / "assets" / "birds"
OUTPUT_DIR = Path(__file__).parent / "output"


def test_orchestrator_end_to_end(db: sqlite3.Connection) -> None:
    """Full cycle: capture -> analyze -> store -> rank -> render -> display."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = Config(assets_dir=ASSETS_DIR, output_dir=OUTPUT_DIR)

    now = datetime.now()
    detections = [
        Detection("Bald Eagle", "Haliaeetus leucocephalus", 0.92, now),
        Detection("Blue Jay", "Cyanocitta cristata", 0.88, now),
        Detection("House Finch", "Haemorhous mexicanus", 0.75, now),
    ]

    repo = SQLiteDetectionRepository(db)
    driver = FileDisplayDriver(OUTPUT_DIR)

    orchestrator = Orchestrator(
        config=config,
        repository=repo,
        renderer=PillowRenderer(),
        display=driver,
        audio=CountingFakeAudio(),
        analyzer=FakeAnalyzer(detections),
    )

    orchestrator.run_once()

    counts = repo.get_lifetime_counts()
    assert "Bald Eagle" in counts
    assert "Blue Jay" in counts
    assert "House Finch" in counts

    output_path = OUTPUT_DIR / "display.png"
    assert output_path.exists()
    img = Image.open(output_path)
    assert img.size == (config.display_width, config.display_height)


def test_orchestrator_no_detections(db: sqlite3.Connection) -> None:
    """Cycle with no bird detections still renders gracefully."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = Config(assets_dir=ASSETS_DIR, output_dir=OUTPUT_DIR)
    repo = SQLiteDetectionRepository(db)
    driver = FileDisplayDriver(OUTPUT_DIR)

    orchestrator = Orchestrator(
        config=config,
        repository=repo,
        renderer=PillowRenderer(),
        display=driver,
        audio=CountingFakeAudio(),
        analyzer=FakeAnalyzer([]),
    )

    orchestrator.run_once()

    output_path = OUTPUT_DIR / "display.png"
    assert output_path.exists()


def test_continuous_capture_no_gaps(db: sqlite3.Connection) -> None:
    """Capture thread runs continuously while analysis happens."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = Config(assets_dir=ASSETS_DIR, output_dir=OUTPUT_DIR)
    audio = CountingFakeAudio()
    analyzer = SlowFakeAnalyzer([], delay=0.1)
    repo = SQLiteDetectionRepository(db)
    driver = FileDisplayDriver(OUTPUT_DIR)

    orchestrator = Orchestrator(
        config=config,
        repository=repo,
        renderer=PillowRenderer(),
        display=driver,
        audio=audio,
        analyzer=analyzer,
    )

    # Run loop briefly in a thread, then stop it
    def run_briefly():
        orchestrator.run_loop()

    orchestrator._stop.clear()
    t = threading.Thread(target=run_briefly, daemon=True)
    t.start()

    # Let it run for 0.8s — capture is 0.05s each, analysis is 0.1s + render
    time.sleep(0.8)
    orchestrator._stop.set()
    t.join(timeout=2)

    # Capture should have been called many times (continuous, not gated by analysis)
    assert audio.call_count >= 5, (
        f"Expected continuous capture (>=5 calls), got {audio.call_count}"
    )
    # Analysis should have processed at least a couple chunks
    assert analyzer.call_count >= 2, (
        f"Expected multiple analysis cycles (>=2), got {analyzer.call_count}"
    )


def test_capture_overlaps_analysis(db: sqlite3.Connection) -> None:
    """Verify capture happens during analysis (not sequentially)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = Config(assets_dir=ASSETS_DIR, output_dir=OUTPUT_DIR)
    audio = CountingFakeAudio()
    # Analysis takes 0.2s per chunk
    analyzer = SlowFakeAnalyzer([], delay=0.2)
    repo = SQLiteDetectionRepository(db)
    driver = FileDisplayDriver(OUTPUT_DIR)

    orchestrator = Orchestrator(
        config=config,
        repository=repo,
        renderer=PillowRenderer(),
        display=driver,
        audio=audio,
        analyzer=analyzer,
    )

    orchestrator._stop.clear()
    t = threading.Thread(target=orchestrator.run_loop, daemon=True)
    t.start()

    time.sleep(0.6)
    orchestrator._stop.set()
    t.join(timeout=2)

    # If capture and analysis were sequential with 0.2s analysis + 0.05s capture,
    # we'd get ~0.6/0.25 = 2 captures. With overlap we should get many more.
    assert audio.call_count > analyzer.call_count, (
        f"Capture ({audio.call_count}) should outpace analysis ({analyzer.call_count}) "
        f"since they run in parallel"
    )
