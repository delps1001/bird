from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

import pytest

from bird_listener.persistence.birdnetpi_repository import BirdNetPiRepository
from bird_listener.persistence.models import Detection

BIRDNETPI_SCHEMA = """\
CREATE TABLE IF NOT EXISTS detections (
  Date DATE,
  Time TIME,
  Sci_Name VARCHAR(100) NOT NULL,
  Com_Name VARCHAR(100) NOT NULL,
  Confidence FLOAT,
  Lat FLOAT,
  Lon FLOAT,
  Cutoff FLOAT,
  Week INT,
  Sens FLOAT,
  Overlap FLOAT,
  File_Name VARCHAR(100) NOT NULL
);
"""


def _seed(conn: sqlite3.Connection, com: str, sci: str, conf: float, dt: datetime) -> None:
    conn.execute(
        "INSERT INTO detections (Date, Time, Sci_Name, Com_Name, Confidence, "
        "Lat, Lon, Cutoff, Week, Sens, Overlap, File_Name) "
        "VALUES (?, ?, ?, ?, ?, 0, 0, 0, 1, 1.0, 0, 'test.wav')",
        (dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), sci, com, conf),
    )
    conn.commit()


@pytest.fixture
def birdnetpi_db(tmp_path):
    """Create a BirdNET-Pi-schema SQLite DB on disk (read-only repo needs a file)."""
    db_path = tmp_path / "birds.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(BIRDNETPI_SCHEMA)
    conn.commit()
    conn.close()
    return db_path


def test_get_detections_since(birdnetpi_db):
    # Seed data via a writable connection
    conn = sqlite3.connect(str(birdnetpi_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "House Finch", "Haemorhous mexicanus", 0.92, now)
    _seed(conn, "Old Bird", "Oldus birdus", 0.80, now - timedelta(hours=25))
    conn.close()

    repo = BirdNetPiRepository(birdnetpi_db)
    results = repo.get_detections_since(now - timedelta(hours=24))

    assert len(results) == 1
    assert results[0].common_name == "House Finch"
    assert results[0].scientific_name == "Haemorhous mexicanus"
    assert results[0].confidence == 0.92
    assert results[0].detected_at == now


def test_get_detections_since_ordering(birdnetpi_db):
    conn = sqlite3.connect(str(birdnetpi_db))
    base = datetime(2026, 4, 10, 10, 0, 0)
    _seed(conn, "First", "Firstus", 0.9, base)
    _seed(conn, "Second", "Secondus", 0.8, base + timedelta(hours=1))
    _seed(conn, "Third", "Thirdus", 0.7, base + timedelta(hours=2))
    conn.close()

    repo = BirdNetPiRepository(birdnetpi_db)
    results = repo.get_detections_since(base - timedelta(hours=1))

    assert len(results) == 3
    # Most recent first
    assert results[0].common_name == "Third"
    assert results[2].common_name == "First"


def test_get_lifetime_counts(birdnetpi_db):
    conn = sqlite3.connect(str(birdnetpi_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    for i in range(5):
        _seed(conn, "House Finch", "Haemorhous mexicanus", 0.9, now + timedelta(minutes=i))
    for i in range(2):
        _seed(conn, "Blue Jay", "Cyanocitta cristata", 0.8, now + timedelta(minutes=i))
    conn.close()

    repo = BirdNetPiRepository(birdnetpi_db)
    counts = repo.get_lifetime_counts()

    assert counts["House Finch"] == 5
    assert counts["Blue Jay"] == 2


def test_record_detection_raises(birdnetpi_db):
    repo = BirdNetPiRepository(birdnetpi_db)
    det = Detection("Test", "Testus", 0.5, datetime.now())
    with pytest.raises(NotImplementedError):
        repo.record_detection(det)


def test_empty_db(birdnetpi_db):
    repo = BirdNetPiRepository(birdnetpi_db)
    assert repo.get_detections_since(datetime(2020, 1, 1)) == []
    assert repo.get_lifetime_counts() == {}


def test_min_confidence_filters_detections(birdnetpi_db):
    conn = sqlite3.connect(str(birdnetpi_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "Confident Bird", "Confidentus", 0.95, now)
    _seed(conn, "Uncertain Bird", "Uncertainus", 0.40, now)
    _seed(conn, "Borderline Bird", "Borderus", 0.70, now)
    conn.close()

    repo = BirdNetPiRepository(birdnetpi_db, min_confidence=0.70)

    results = repo.get_detections_since(now - timedelta(hours=1))
    names = [r.common_name for r in results]
    assert "Confident Bird" in names
    assert "Borderline Bird" in names
    assert "Uncertain Bird" not in names

    counts = repo.get_lifetime_counts()
    assert "Confident Bird" in counts
    assert "Borderline Bird" in counts
    assert "Uncertain Bird" not in counts
