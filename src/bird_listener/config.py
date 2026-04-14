from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    lat: float = 35.78
    lon: float = -78.64
    min_confidence: float = 0.80
    display_width: int = 800
    display_height: int = 480
    assets_dir: Path = field(default_factory=lambda: Path("assets/birds"))
    output_dir: Path = field(default_factory=lambda: Path("output"))
    db_path: Path = field(default_factory=lambda: Path("detections.db"))
    capture_duration_sec: int = 15
    capture_overlap_sec: int = 3  # overlap between consecutive chunks
    loop_interval_sec: int = 30
    recent_window_hours: int = 144
    display_renderer: str = "fieldguide"
    boundary_inset: float = .07
