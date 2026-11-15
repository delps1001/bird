from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Detection:
    common_name: str
    scientific_name: str
    confidence: float
    detected_at: datetime
    id: int | None = None  # source-database row id, when the backend has one


@dataclass(frozen=True)
class BirdSummary:
    common_name: str
    scientific_name: str
    lifetime_count: int
    recent_count: int
    best_confidence: float
    last_detected_at: datetime | None = None
    is_new: bool = False
    last_detection_id: int | None = None
