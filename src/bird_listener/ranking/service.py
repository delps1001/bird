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
        summaries.append(
            BirdSummary(
                common_name=name,
                scientific_name=best.scientific_name,
                lifetime_count=lifetime_counts.get(name, 0),
                recent_count=len(detections),
                best_confidence=best.confidence,
            )
        )

    # Sort: rarest first (lowest lifetime count), then by best confidence descending
    summaries.sort(key=lambda s: (s.lifetime_count, -s.best_confidence))
    return summaries
