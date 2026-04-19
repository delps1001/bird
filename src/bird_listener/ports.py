from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from PIL import Image

from bird_listener.persistence.models import BirdSummary, Detection


@runtime_checkable
class AudioSource(Protocol):
    def capture(self) -> tuple[bytes, int]:
        """Return (WAV bytes, sample rate)."""
        ...


@runtime_checkable
class BirdAnalyzer(Protocol):
    def analyze(
        self,
        wav_data: bytes,
        lat: float,
        lon: float,
        date: datetime,
        min_conf: float,
    ) -> list[Detection]:
        ...


@runtime_checkable
class DetectionRepository(Protocol):
    def record_detection(self, detection: Detection) -> None:
        ...

    def get_detections_since(self, since: datetime) -> list[Detection]:
        ...

    def get_lifetime_counts(self) -> dict[str, int]:
        """Return {common_name: total_count} for all species ever detected."""
        ...

    def get_first_detection_times(self) -> dict[str, datetime]:
        """Return {common_name: earliest_detected_at} for all species ever detected."""
        ...


@runtime_checkable
class DisplayRenderer(Protocol):
    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        ...


@runtime_checkable
class DisplayDriver(Protocol):
    def show(self, image: Image.Image) -> None:
        ...
