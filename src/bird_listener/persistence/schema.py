from __future__ import annotations

import sqlite3
from pathlib import Path

DDL = """\
CREATE TABLE IF NOT EXISTS detections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    common_name   TEXT    NOT NULL,
    scientific_name TEXT  NOT NULL,
    confidence    REAL    NOT NULL,
    detected_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_detections_detected_at
    ON detections (detected_at);

CREATE INDEX IF NOT EXISTS idx_detections_common_name
    ON detections (common_name);
"""


def init_db(db_path: Path | str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.executescript(DDL)
    return conn
