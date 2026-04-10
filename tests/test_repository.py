from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from bird_listener.persistence.models import Detection
from bird_listener.persistence.repository import SQLiteDetectionRepository


def test_record_and_retrieve(db: sqlite3.Connection) -> None:
    repo = SQLiteDetectionRepository(db)
    det = Detection(
        common_name="House Finch",
        scientific_name="Haemorhous mexicanus",
        confidence=0.85,
        detected_at=datetime(2026, 4, 6, 12, 0, 0),
    )
    repo.record_detection(det)

    results = repo.get_detections_since(datetime(2026, 4, 6, 0, 0, 0))
    assert len(results) == 1
    assert results[0].common_name == "House Finch"
    assert results[0].confidence == 0.85


def test_get_detections_since_filters_old(db: sqlite3.Connection) -> None:
    repo = SQLiteDetectionRepository(db)
    now = datetime(2026, 4, 6, 12, 0, 0)

    repo.record_detection(Detection("Old Bird", "Oldus birdus", 0.9, now - timedelta(hours=25)))
    repo.record_detection(Detection("New Bird", "Newus birdus", 0.8, now - timedelta(hours=1)))

    results = repo.get_detections_since(now - timedelta(hours=24))
    assert len(results) == 1
    assert results[0].common_name == "New Bird"


def test_lifetime_counts(db: sqlite3.Connection) -> None:
    repo = SQLiteDetectionRepository(db)
    now = datetime(2026, 4, 6, 12, 0, 0)

    for i in range(5):
        repo.record_detection(Detection("House Finch", "Haemorhous mexicanus", 0.8, now + timedelta(minutes=i)))
    for i in range(2):
        repo.record_detection(Detection("Blue Jay", "Cyanocitta cristata", 0.7, now + timedelta(minutes=i)))

    counts = repo.get_lifetime_counts()
    assert counts["House Finch"] == 5
    assert counts["Blue Jay"] == 2


def test_empty_db(db: sqlite3.Connection) -> None:
    repo = SQLiteDetectionRepository(db)
    assert repo.get_detections_since(datetime(2020, 1, 1)) == []
    assert repo.get_lifetime_counts() == {}
