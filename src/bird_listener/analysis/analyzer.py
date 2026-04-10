from __future__ import annotations

import csv
import tempfile
from datetime import datetime
from pathlib import Path

from bird_listener.persistence.models import Detection


def _deduplicate(detections: list[Detection]) -> list[Detection]:
    """Keep only the highest-confidence detection per species."""
    best: dict[str, Detection] = {}
    for d in detections:
        if d.common_name not in best or d.confidence > best[d.common_name].confidence:
            best[d.common_name] = d
    return list(best.values())


class BirdNetAnalyzer:
    """Wraps birdnet-analyzer (v2.4+) for bird species detection."""

    def analyze(
        self,
        wav_data: bytes,
        lat: float,
        lon: float,
        date: datetime,
        min_conf: float,
    ) -> list[Detection]:
        from birdnet_analyzer import analyze

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_data)
            wav_path = Path(f.name)

        out_dir = Path(tempfile.mkdtemp())
        try:
            week = date.isocalendar()[1]
            analyze(
                str(wav_path),
                str(out_dir),
                rtype="csv",
                lat=lat,
                lon=lon,
                week=week,
                min_conf=min_conf,
                overlap=1.5,  # 1.5s overlap between 3s analysis windows
                top_n=3,  # return up to 3 species per 3s window
            )

            now = datetime.now()
            detections: list[Detection] = []
            for csv_file in out_dir.glob("*.csv"):
                with open(csv_file) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        common = row.get("Common name", row.get("common_name", ""))
                        scientific = row.get("Scientific name", row.get("scientific_name", ""))
                        conf = float(row.get("Confidence", row.get("confidence", 0)))
                        if common and conf >= min_conf:
                            detections.append(
                                Detection(
                                    common_name=common,
                                    scientific_name=scientific,
                                    confidence=conf,
                                    detected_at=now,
                                )
                            )
            return _deduplicate(detections)
        finally:
            wav_path.unlink(missing_ok=True)
            for f in out_dir.iterdir():
                f.unlink(missing_ok=True)
            out_dir.rmdir()


class BirdNetLibAnalyzer:
    """Wraps birdnetlib (v0.18) — legacy fallback, bundles its own model."""

    def __init__(self) -> None:
        from birdnetlib.analyzer import Analyzer

        self._analyzer = Analyzer()

    def analyze(
        self,
        wav_data: bytes,
        lat: float,
        lon: float,
        date: datetime,
        min_conf: float,
    ) -> list[Detection]:
        from birdnetlib import Recording

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_data)
            tmp_path = Path(f.name)

        try:
            recording = Recording(
                self._analyzer,
                str(tmp_path),
                lat=lat,
                lon=lon,
                date=date,
                min_conf=min_conf,
            )
            recording.analyze()

            now = datetime.now()
            return _deduplicate([
                Detection(
                    common_name=d["common_name"],
                    scientific_name=d["scientific_name"],
                    confidence=d["confidence"],
                    detected_at=now,
                )
                for d in recording.detections
            ])
        finally:
            tmp_path.unlink(missing_ok=True)
