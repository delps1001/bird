from __future__ import annotations

from datetime import datetime

from bird_listener.persistence.models import BirdSummary, Detection


def rank_birds(
    recent_detections: list[Detection],
    lifetime_counts: dict[str, int],
) -> list[BirdSummary]:
    """Rank birds by rarity (lowest lifetime count = rarest first)."""
    # Group recent detections by species
    species: dict[str, list[Detection]] = {}
    for d in recent_detections:
        species.setdefault(d.common_name, []).append(d)

    summaries = []
    for name, detections in species.items():
        best = max(detections, key=lambda d: d.confidence)
        latest = max(detections, key=lambda d: d.detected_at)
        summaries.append(
            BirdSummary(
                common_name=name,
                scientific_name=best.scientific_name,
                lifetime_count=lifetime_counts.get(name, 0),
                recent_count=len(detections),
                best_confidence=best.confidence,
                last_detected_at=latest.detected_at,
            )
        )

    # Sort: rarest first, then most-recently-seen, then best confidence descending
    summaries.sort(key=lambda s: (
        s.lifetime_count,
        -(s.last_detected_at.timestamp() if s.last_detected_at else 0),
        -s.best_confidence,
    ))
    return summaries
