from __future__ import annotations

import sqlite3
from datetime import datetime

from bird_listener.persistence.models import Detection


class SQLiteDetectionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def record_detection(self, detection: Detection) -> None:
        self._conn.execute(
            "INSERT INTO detections (common_name, scientific_name, confidence, detected_at) "
            "VALUES (?, ?, ?, ?)",
            (
                detection.common_name,
                detection.scientific_name,
                detection.confidence,
                detection.detected_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_detections_since(self, since: datetime) -> list[Detection]:
        rows = self._conn.execute(
            "SELECT common_name, scientific_name, confidence, detected_at "
            "FROM detections WHERE detected_at >= ? ORDER BY detected_at DESC",
            (since.isoformat(),),
        ).fetchall()
        return [
            Detection(
                common_name=r[0],
                scientific_name=r[1],
                confidence=r[2],
                detected_at=datetime.fromisoformat(r[3]),
            )
            for r in rows
        ]

    def get_lifetime_counts(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT common_name, COUNT(*) FROM detections GROUP BY common_name"
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def get_lifetime_unique_days(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT common_name, COUNT(DISTINCT substr(detected_at, 1, 10)) "
            "FROM detections GROUP BY common_name"
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def get_first_detection_times(self) -> dict[str, datetime]:
        rows = self._conn.execute(
            "SELECT common_name, MIN(detected_at) FROM detections GROUP BY common_name"
        ).fetchall()
        return {r[0]: datetime.fromisoformat(r[1]) for r in rows}
