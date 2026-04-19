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


def test_new_bird_outranks_rarer_old_bird() -> None:
    """A newly-recognized species always ranks above established species,
    even a much rarer one."""
    now = datetime(2026, 4, 19, 12, 0)
    since = datetime(2026, 4, 18, 12, 0)
    detections = [
        Detection("Newcomer", "N n", 0.7, now),
        Detection("Rare Old", "R o", 0.9, now),
    ]
    lifetime_counts = {"Newcomer": 1, "Rare Old": 1}
    first_seen = {
        "Newcomer": now,                       # first-ever, inside window
        "Rare Old": datetime(2020, 1, 1),      # long-established
    }

    ranked = rank_birds(detections, lifetime_counts, first_seen=first_seen, new_since=since)

    assert ranked[0].common_name == "Newcomer"
    assert ranked[0].is_new is True
    assert ranked[1].common_name == "Rare Old"
    assert ranked[1].is_new is False


def test_multiple_new_birds_tiebreak_by_most_recent() -> None:
    now = datetime(2026, 4, 19, 12, 0)
    since = datetime(2026, 4, 18, 12, 0)
    detections = [
        Detection("Early New", "E n", 0.9, datetime(2026, 4, 19, 8, 0)),
        Detection("Late New", "L n", 0.6, datetime(2026, 4, 19, 11, 0)),
        Detection("Mid New", "M n", 0.7, datetime(2026, 4, 19, 10, 0)),
    ]
    first_seen = {
        "Early New": datetime(2026, 4, 19, 8, 0),
        "Late New": datetime(2026, 4, 19, 11, 0),
        "Mid New": datetime(2026, 4, 19, 10, 0),
    }

    ranked = rank_birds(detections, {}, first_seen=first_seen, new_since=since)

    assert [b.common_name for b in ranked] == ["Late New", "Mid New", "Early New"]
    assert all(b.is_new for b in ranked)


def test_bird_first_seen_before_window_is_not_new() -> None:
    now = datetime(2026, 4, 19, 12, 0)
    since = datetime(2026, 4, 18, 12, 0)
    detections = [
        Detection("Familiar", "F f", 0.9, now),
    ]
    first_seen = {"Familiar": datetime(2026, 4, 17, 23, 59)}  # just before window

    ranked = rank_birds(detections, {"Familiar": 3}, first_seen=first_seen, new_since=since)

    assert len(ranked) == 1
    assert ranked[0].is_new is False


def test_no_new_since_means_no_new_birds() -> None:
    """Default call signature (no new_since) never marks anything as new."""
    now = datetime(2026, 4, 19, 12, 0)
    detections = [Detection("Bird", "B b", 0.9, now)]
    first_seen = {"Bird": now}

    ranked = rank_birds(detections, {"Bird": 1}, first_seen=first_seen)

    assert ranked[0].is_new is False
