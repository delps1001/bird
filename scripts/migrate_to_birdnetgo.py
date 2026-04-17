#!/usr/bin/env python3
"""Migrate bird-listener detections.db → BirdNET-Go v2 normalized schema.

Usage:
    python scripts/migrate_to_birdnetgo.py detections.db birdnetgo.db

Reads the flat ``detections`` table from a bird-listener database and writes
into a new SQLite file using BirdNET-Go's normalized v2 schema.

A default AI model (BirdNET 2.4) and audio source are created as
placeholder reference rows so that foreign-key constraints are satisfied.
Each unique ``scientific_name`` gets its own ``labels`` row.  The original
``common_name`` is **not** stored in BirdNET-Go's schema (it resolves
common names from external label files at runtime).
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BIRDNETGO_DDL = """\
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

CREATE INDEX IF NOT EXISTS idx_detection_model_label
    ON detections (model_id, label_id);
CREATE INDEX IF NOT EXISTS idx_detection_label_date
    ON detections (label_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_detection_confidence
    ON detections (detected_at, confidence);
CREATE INDEX IF NOT EXISTS idx_detection_source
    ON detections (source_id);
"""

MODEL_ID = 1
LABEL_TYPE_ID = 1
TAXONOMIC_CLASS_ID = 1
SOURCE_ID = 1


def _init_dest(conn: sqlite3.Connection) -> None:
    """Create the v2 schema and insert reference/lookup rows."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(BIRDNETGO_DDL)

    conn.execute("INSERT INTO label_types (id, name) VALUES (?, 'species')", (LABEL_TYPE_ID,))
    conn.execute("INSERT INTO taxonomic_classes (id, name) VALUES (?, 'Aves')", (TAXONOMIC_CLASS_ID,))
    conn.execute(
        "INSERT INTO ai_models (id, name, version, variant, model_type) "
        "VALUES (?, 'BirdNET', '2.4', 'default', 'bird')",
        (MODEL_ID,),
    )
    conn.execute(
        "INSERT INTO audio_sources (id, source_uri, node_name, source_type, display_name) "
        "VALUES (?, 'migrated://bird-listener', 'bird-listener', 'unknown', 'Migrated from bird-listener')",
        (SOURCE_ID,),
    )
    conn.commit()


def _get_or_create_label(conn: sqlite3.Connection, sci_name: str, cache: dict[str, int]) -> int:
    """Return the label id for *sci_name*, creating the row if needed."""
    if sci_name in cache:
        return cache[sci_name]
    cur = conn.execute(
        "INSERT INTO labels (scientific_name, model_id, label_type_id, taxonomic_class_id) "
        "VALUES (?, ?, ?, ?)",
        (sci_name, MODEL_ID, LABEL_TYPE_ID, TAXONOMIC_CLASS_ID),
    )
    label_id = cur.lastrowid
    cache[sci_name] = label_id
    return label_id


def migrate(src_path: Path, dest_path: Path) -> int:
    """Migrate detections from *src_path* to *dest_path*.  Returns row count."""
    if dest_path.exists():
        print(f"Error: destination {dest_path} already exists. Remove it first.", file=sys.stderr)
        sys.exit(1)

    src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
    dest = sqlite3.connect(str(dest_path))

    _init_dest(dest)

    rows = src.execute(
        "SELECT id, common_name, scientific_name, confidence, detected_at "
        "FROM detections ORDER BY id"
    ).fetchall()

    label_cache: dict[str, int] = {}
    count = 0

    for row_id, _common_name, sci_name, confidence, detected_at_iso in rows:
        label_id = _get_or_create_label(dest, sci_name, label_cache)
        dt = datetime.fromisoformat(detected_at_iso)
        ts = int(dt.replace(tzinfo=timezone.utc).timestamp())
        dest.execute(
            "INSERT INTO detections (model_id, label_id, source_id, detected_at, confidence, legacy_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (MODEL_ID, label_id, SOURCE_ID, ts, confidence, row_id),
        )
        count += 1

    dest.commit()
    src.close()
    dest.close()

    print(f"Migrated {count} detections ({len(label_cache)} unique species) → {dest_path}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate bird-listener detections.db to BirdNET-Go v2 schema"
    )
    parser.add_argument("source", type=Path, help="Path to bird-listener detections.db")
    parser.add_argument("destination", type=Path, help="Path for new BirdNET-Go database")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Error: source database {args.source} not found.", file=sys.stderr)
        sys.exit(1)

    migrate(args.source, args.destination)


if __name__ == "__main__":
    main()
