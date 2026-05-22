from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from bird_listener.persistence.models import Detection


class BirdNetPiRepository:
    """Read-only repository that queries BirdNET-Pi's birds.db schema."""

    def __init__(self, db_path: Path, min_confidence: float = 0.0) -> None:
        uri = f"file:{db_path}?mode=ro"
        self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self._min_confidence = min_confidence

    def record_detection(self, detection: Detection) -> None:
        raise NotImplementedError("BirdNET-Pi repository is read-only")

    def get_detections_since(self, since: datetime) -> list[Detection]:
        since_str = since.strftime("%Y-%m-%d %H:%M:%S")
        rows = self._conn.execute(
            "SELECT Date, Time, Com_Name, Sci_Name, Confidence "
            "FROM detections "
            "WHERE Date || ' ' || Time >= ? AND Confidence >= ? "
            "ORDER BY Date DESC, Time DESC",
            (since_str, self._min_confidence),
        ).fetchall()
        return [
            Detection(
                common_name=row[2],
                scientific_name=row[3],
                confidence=row[4],
                detected_at=datetime.strptime(
                    f"{row[0]} {row[1]}", "%Y-%m-%d %H:%M:%S"
                ),
            )
            for row in rows
        ]

    def get_lifetime_counts(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT Com_Name, COUNT(*) FROM detections "
            "WHERE Confidence >= ? GROUP BY Com_Name",
            (self._min_confidence,),
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    def get_lifetime_unique_days(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT Com_Name, COUNT(DISTINCT Date) FROM detections "
            "WHERE Confidence >= ? GROUP BY Com_Name",
            (self._min_confidence,),
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    def get_first_detection_times(self) -> dict[str, datetime]:
        rows = self._conn.execute(
            "SELECT Com_Name, MIN(Date || ' ' || Time) FROM detections "
            "WHERE Confidence >= ? GROUP BY Com_Name",
            (self._min_confidence,),
        ).fetchall()
        return {
            row[0]: datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            for row in rows
        }
