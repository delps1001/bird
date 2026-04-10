from __future__ import annotations

from datetime import datetime

from bird_listener.persistence.models import BirdSummary, Detection
from bird_listener.ranking.service import rank_birds


def test_rank_by_rarity() -> None:
    detections = [
        Detection("House Finch", "Haemorhous mexicanus", 0.9, datetime(2026, 4, 6, 12, 0)),
        Detection("Bald Eagle", "Haliaeetus leucocephalus", 0.7, datetime(2026, 4, 6, 12, 5)),
        Detection("House Finch", "Haemorhous mexicanus", 0.8, datetime(2026, 4, 6, 12, 10)),
    ]
    lifetime_counts = {"House Finch": 100, "Bald Eagle": 1}

    ranked = rank_birds(detections, lifetime_counts)

    assert len(ranked) == 2
    assert ranked[0].common_name == "Bald Eagle"  # rarest
    assert ranked[1].common_name == "House Finch"  # most common


def test_rank_tiebreaker_by_confidence() -> None:
    detections = [
        Detection("Bird A", "A a", 0.9, datetime(2026, 4, 6, 12, 0)),
        Detection("Bird B", "B b", 0.7, datetime(2026, 4, 6, 12, 0)),
    ]
    lifetime_counts = {"Bird A": 5, "Bird B": 5}

    ranked = rank_birds(detections, lifetime_counts)
    assert ranked[0].common_name == "Bird A"  # higher confidence wins tie


def test_rank_empty() -> None:
    assert rank_birds([], {}) == []


def test_best_confidence_selected() -> None:
    detections = [
        Detection("Finch", "F f", 0.5, datetime(2026, 4, 6, 12, 0)),
        Detection("Finch", "F f", 0.95, datetime(2026, 4, 6, 12, 5)),
        Detection("Finch", "F f", 0.7, datetime(2026, 4, 6, 12, 10)),
    ]
    ranked = rank_birds(detections, {"Finch": 10})
    assert ranked[0].best_confidence == 0.95
    assert ranked[0].recent_count == 3
