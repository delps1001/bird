from __future__ import annotations

from datetime import datetime

from bird_listener.persistence.models import BirdSummary, Detection


def rank_birds(
    recent_detections: list[Detection],
    lifetime_counts: dict[str, int],
    first_seen: dict[str, datetime] | None = None,
    new_since: datetime | None = None,
) -> list[BirdSummary]:
    """Rank birds, surfacing newly-recognized species first.

    A species is "new" when its earliest-ever detection (``first_seen[name]``)
    falls on or after ``new_since``. New species are ranked above all others
    and tie-broken by most recent detection. Remaining species follow the
    legacy ordering: rarest first, then most-recent, then highest confidence.
    """
    first_seen = first_seen or {}

    species: dict[str, list[Detection]] = {}
    for d in recent_detections:
        species.setdefault(d.common_name, []).append(d)

    summaries = []
    for name, detections in species.items():
        best = max(detections, key=lambda d: d.confidence)
        latest = max(detections, key=lambda d: d.detected_at)
        first = first_seen.get(name)
        is_new = (
            new_since is not None
            and first is not None
            and first >= new_since
        )
        summaries.append(
            BirdSummary(
                common_name=name,
                scientific_name=best.scientific_name,
                lifetime_count=lifetime_counts.get(name, 0),
                recent_count=len(detections),
                best_confidence=best.confidence,
                last_detected_at=latest.detected_at,
                is_new=is_new,
            )
        )

    new_birds = [s for s in summaries if s.is_new]
    other_birds = [s for s in summaries if not s.is_new]

    new_birds.sort(key=lambda s: -(
        s.last_detected_at.timestamp() if s.last_detected_at else 0
    ))
    other_birds.sort(key=lambda s: (
        s.lifetime_count,
        -(s.last_detected_at.timestamp() if s.last_detected_at else 0),
        -s.best_confidence,
    ))
    return new_birds + other_birds
