from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from bird_listener.persistence.birdnetgo_repository import BirdNetGoRepository, load_label_map
from bird_listener.persistence.models import Detection

# Minimal BirdNET-Go v2 normalized schema (only tables the repository queries).
BIRDNETGO_SCHEMA = """\
CREATE TABLE IF NOT EXISTS label_types (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS taxonomic_classes (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS ai_models (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(50)  NOT NULL,
    version         VARCHAR(20)  NOT NULL,
    variant         VARCHAR(100) NOT NULL DEFAULT 'default',
    model_type      VARCHAR(20)  NOT NULL,
    classifier_path VARCHAR(500),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, version, variant)
);

CREATE TABLE IF NOT EXISTS audio_sources (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_uri   VARCHAR(500) NOT NULL,
    node_name    VARCHAR(100) NOT NULL,
    source_type  VARCHAR(20)  NOT NULL,
    display_name VARCHAR(200),
    config_json  TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_uri, node_name)
);

CREATE TABLE IF NOT EXISTS labels (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name    VARCHAR(200) NOT NULL,
    model_id           BIGINT       NOT NULL REFERENCES ai_models(id),
    label_type_id      BIGINT       NOT NULL REFERENCES label_types(id),
    taxonomic_class_id BIGINT                REFERENCES taxonomic_classes(id),
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (scientific_name, model_id)
);

CREATE TABLE IF NOT EXISTS detections (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id           BIGINT  NOT NULL REFERENCES ai_models(id) ON DELETE CASCADE,
    label_id           BIGINT  NOT NULL REFERENCES labels(id)    ON DELETE CASCADE,
    source_id          BIGINT           REFERENCES audio_sources(id),
    detected_at        BIGINT  NOT NULL,
    begin_time         BIGINT,
    end_time           BIGINT,
    confidence         DOUBLE  NOT NULL,
    latitude           DOUBLE,
    longitude          DOUBLE,
    clip_name          VARCHAR(500),
    processing_time_ms BIGINT,
    legacy_id          BIGINT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_detection_confidence
    ON detections (detected_at, confidence);
"""

# Small label file used by tests so common name resolution is exercised.
TEST_LABELS = (
    "Haemorhous mexicanus_House Finch\n"
    "Cyanocitta cristata_Blue Jay\n"
    "Cardinalis cardinalis_Northern Cardinal\n"
    "Sitta carolinensis_White-breasted Nuthatch\n"
)


def _bootstrap(conn: sqlite3.Connection) -> None:
    """Insert reference rows needed by foreign keys."""
    conn.execute("INSERT INTO label_types (id, name) VALUES (1, 'species')")
    conn.execute("INSERT INTO taxonomic_classes (id, name) VALUES (1, 'Aves')")
    conn.execute(
        "INSERT INTO ai_models (id, name, version, variant, model_type) "
        "VALUES (1, 'BirdNET', '2.4', 'default', 'bird')"
    )
    conn.execute(
        "INSERT INTO audio_sources (id, source_uri, node_name, source_type) "
        "VALUES (1, 'alsa://default', 'node1', 'alsa')"
    )
    conn.commit()


def _ensure_label(conn: sqlite3.Connection, sci_name: str, model_id: int = 1) -> int:
    """Return the label id, creating the row if needed."""
    row = conn.execute(
        "SELECT id FROM labels WHERE scientific_name = ? AND model_id = ?",
        (sci_name, model_id),
    ).fetchone()
    if row:
        return row[0]
    cur = conn.execute(
        "INSERT INTO labels (scientific_name, model_id, label_type_id, taxonomic_class_id) "
        "VALUES (?, ?, 1, 1)",
        (sci_name, model_id),
    )
    conn.commit()
    return cur.lastrowid


def _seed(
    conn: sqlite3.Connection,
    sci_name: str,
    conf: float,
    dt: datetime,
    *,
    model_id: int = 1,
    source_id: int = 1,
) -> None:
    """Insert a detection row with its label."""
    label_id = _ensure_label(conn, sci_name, model_id)
    ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
    conn.execute(
        "INSERT INTO detections (model_id, label_id, source_id, detected_at, confidence) "
        "VALUES (?, ?, ?, ?, ?)",
        (model_id, label_id, source_id, ts, conf),
    )
    conn.commit()


@pytest.fixture
def label_file(tmp_path) -> Path:
    """Write a small label file and return its path."""
    p = tmp_path / "labels.txt"
    p.write_text(TEST_LABELS)
    return p


@pytest.fixture
def birdnetgo_db(tmp_path):
    """Create a BirdNET-Go v2 schema SQLite DB on disk."""
    db_path = tmp_path / "birdnet.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(BIRDNETGO_SCHEMA)
    _bootstrap(conn)
    conn.close()
    return db_path


# ---- load_label_map -------------------------------------------------------


def test_load_label_map(label_file):
    mapping = load_label_map(label_file)
    assert mapping["Haemorhous mexicanus"] == "House Finch"
    assert mapping["Cyanocitta cristata"] == "Blue Jay"
    assert len(mapping) == 4


# ---- common name resolution -----------------------------------------------


def test_common_name_resolved_from_label_file(birdnetgo_db, label_file):
    conn = sqlite3.connect(str(birdnetgo_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "Haemorhous mexicanus", 0.92, now)
    _seed(conn, "Cyanocitta cristata", 0.85, now + timedelta(seconds=1))
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    results = repo.get_detections_since(now - timedelta(hours=1))

    by_sci = {r.scientific_name: r for r in results}
    assert by_sci["Haemorhous mexicanus"].common_name == "House Finch"
    assert by_sci["Cyanocitta cristata"].common_name == "Blue Jay"


def test_common_name_falls_back_to_scientific(birdnetgo_db, label_file):
    """Species not in the label file should fall back to scientific name."""
    conn = sqlite3.connect(str(birdnetgo_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "Unknownus birdus", 0.90, now)
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    results = repo.get_detections_since(now - timedelta(hours=1))

    assert len(results) == 1
    assert results[0].common_name == "Unknownus birdus"
    assert results[0].scientific_name == "Unknownus birdus"


def test_lifetime_counts_keyed_by_common_name(birdnetgo_db, label_file):
    conn = sqlite3.connect(str(birdnetgo_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    for i in range(5):
        _seed(conn, "Haemorhous mexicanus", 0.9, now + timedelta(minutes=i))
    for i in range(2):
        _seed(conn, "Cyanocitta cristata", 0.8, now + timedelta(minutes=i))
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    counts = repo.get_lifetime_counts()

    assert counts["House Finch"] == 5
    assert counts["Blue Jay"] == 2


# ---- get_detections_since -------------------------------------------------


def test_get_detections_since(birdnetgo_db, label_file):
    conn = sqlite3.connect(str(birdnetgo_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "Haemorhous mexicanus", 0.92, now)
    _seed(conn, "Cardinalis cardinalis", 0.80, now - timedelta(hours=25))
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    results = repo.get_detections_since(now - timedelta(hours=24))

    assert len(results) == 1
    assert results[0].common_name == "House Finch"
    assert results[0].scientific_name == "Haemorhous mexicanus"
    assert results[0].confidence == 0.92
    assert results[0].detected_at == now


def test_get_detections_since_ordering(birdnetgo_db, label_file):
    conn = sqlite3.connect(str(birdnetgo_db))
    base = datetime(2026, 4, 10, 10, 0, 0)
    _seed(conn, "Haemorhous mexicanus", 0.9, base)
    _seed(conn, "Cyanocitta cristata", 0.8, base + timedelta(hours=1))
    _seed(conn, "Cardinalis cardinalis", 0.7, base + timedelta(hours=2))
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    results = repo.get_detections_since(base - timedelta(hours=1))

    assert len(results) == 3
    # Most recent first
    assert results[0].common_name == "Northern Cardinal"
    assert results[2].common_name == "House Finch"


# ---- record_detection raises ---------------------------------------------


def test_record_detection_raises(birdnetgo_db, label_file):
    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    det = Detection("Test", "Testus", 0.5, datetime.now())
    with pytest.raises(NotImplementedError):
        repo.record_detection(det)


# ---- empty database -------------------------------------------------------


def test_empty_db(birdnetgo_db, label_file):
    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    assert repo.get_detections_since(datetime(2020, 1, 1)) == []
    assert repo.get_lifetime_counts() == {}


# ---- min_confidence filtering ---------------------------------------------


def test_min_confidence_filters_detections(birdnetgo_db, label_file):
    conn = sqlite3.connect(str(birdnetgo_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "Haemorhous mexicanus", 0.95, now)
    _seed(conn, "Cyanocitta cristata", 0.40, now + timedelta(seconds=1))
    _seed(conn, "Cardinalis cardinalis", 0.70, now + timedelta(seconds=2))
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, min_confidence=0.70, label_file=label_file)

    results = repo.get_detections_since(now - timedelta(hours=1))
    names = [r.common_name for r in results]
    assert "House Finch" in names
    assert "Northern Cardinal" in names
    assert "Blue Jay" not in names

    counts = repo.get_lifetime_counts()
    assert "House Finch" in counts
    assert "Northern Cardinal" in counts
    assert "Blue Jay" not in counts


def test_min_confidence_zero_returns_all(birdnetgo_db, label_file):
    conn = sqlite3.connect(str(birdnetgo_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "Haemorhous mexicanus", 0.10, now)
    _seed(conn, "Cyanocitta cristata", 0.99, now + timedelta(seconds=1))
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, min_confidence=0.0, label_file=label_file)
    results = repo.get_detections_since(now - timedelta(hours=1))
    assert len(results) == 2


# ---- multiple detections of same species ----------------------------------


def test_multiple_detections_same_species_share_label(birdnetgo_db, label_file):
    conn = sqlite3.connect(str(birdnetgo_db))
    now = datetime(2026, 4, 10, 12, 0, 0)
    _seed(conn, "Haemorhous mexicanus", 0.90, now)
    _seed(conn, "Haemorhous mexicanus", 0.85, now + timedelta(minutes=1))
    _seed(conn, "Haemorhous mexicanus", 0.80, now + timedelta(minutes=2))
    conn.close()

    repo = BirdNetGoRepository(birdnetgo_db, label_file=label_file)
    results = repo.get_detections_since(now - timedelta(hours=1))
    assert len(results) == 3
    assert all(r.common_name == "House Finch" for r in results)
    assert all(r.scientific_name == "Haemorhous mexicanus" for r in results)

    counts = repo.get_lifetime_counts()
    assert counts["House Finch"] == 3
