from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from bird_listener.persistence.models import Detection

# Default label file shipped with BirdNET-Go V2.4.
_DEFAULT_LABELS = (
    Path(__file__).resolve().parents[3]
    / "assets"
    / "BirdNET_GLOBAL_6K_V2.4_Labels_en_us.txt"
)


def load_label_map(label_file: Path) -> dict[str, str]:
    """Parse a BirdNET label file into a scientific→common name mapping.

    Each line is ``ScientificName_CommonName``.  Returns a dict keyed by
    scientific name with common name as value.
    """
    mapping: dict[str, str] = {}
    with open(label_file) as f:
        for line in f:
            line = line.strip()
            if "_" in line:
                sci, common = line.split("_", 1)
                mapping[sci] = common
    return mapping


class BirdNetGoRepository:
    """Read-only repository that queries BirdNET-Go's normalized v2 schema.

    BirdNET-Go's ``labels`` table stores only ``scientific_name``.  Common
    names are resolved via a BirdNET label file (``ScientificName_CommonName``
    per line).  Pass *label_file* to override the default bundled labels.
    """

    def __init__(
        self,
        db_path: Path,
        min_confidence: float = 0.0,
        label_file: Path | None = None,
    ) -> None:
        uri = f"file:{db_path}?mode=ro"
        self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._min_confidence = min_confidence
        lf = label_file or _DEFAULT_LABELS
        self._labels = load_label_map(lf) if lf.exists() else {}

    def _common_name(self, scientific_name: str) -> str:
        """Resolve common name, falling back to scientific name."""
        return self._labels.get(scientific_name, scientific_name)

    def record_detection(self, detection: Detection) -> None:
        raise NotImplementedError("BirdNET-Go repository is read-only")

    def get_detections_since(self, since: datetime) -> list[Detection]:
        since_ts = int(since.replace(tzinfo=timezone.utc).timestamp())
        rows = self._conn.execute(
            "SELECT l.scientific_name, d.confidence, d.detected_at "
            "FROM detections d "
            "JOIN labels l ON d.label_id = l.id "
            "WHERE d.detected_at >= ? AND d.confidence >= ? "
            "ORDER BY d.detected_at DESC",
            (since_ts, self._min_confidence),
        ).fetchall()
        return [
            Detection(
                common_name=self._common_name(row[0]),
                scientific_name=row[0],
                confidence=row[1],
                detected_at=datetime.fromtimestamp(row[2], tz=timezone.utc).replace(
                    tzinfo=None
                ),
            )
            for row in rows
        ]

    def get_lifetime_counts(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT l.scientific_name, COUNT(*) "
            "FROM detections d "
            "JOIN labels l ON d.label_id = l.id "
            "WHERE d.confidence >= ? "
            "GROUP BY l.scientific_name",
            (self._min_confidence,),
        ).fetchall()
        return {self._common_name(row[0]): row[1] for row in rows}
