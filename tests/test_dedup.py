from __future__ import annotations

from datetime import datetime

from bird_listener.analysis.analyzer import _deduplicate
from bird_listener.persistence.models import Detection


def test_deduplicate_keeps_best_confidence() -> None:
    now = datetime(2026, 4, 6, 12, 0)
    detections = [
        Detection("Barred Owl", "Strix varia", 0.70, now),
        Detection("Barred Owl", "Strix varia", 0.99, now),
        Detection("Barred Owl", "Strix varia", 0.89, now),
    ]
    result = _deduplicate(detections)
    assert len(result) == 1
    assert result[0].confidence == 0.99


def test_deduplicate_preserves_different_species() -> None:
    now = datetime(2026, 4, 6, 12, 0)
    detections = [
        Detection("Barred Owl", "Strix varia", 0.94, now),
        Detection("Barred Owl", "Strix varia", 0.70, now),
        Detection("Rock Pigeon", "Columba livia", 0.64, now),
    ]
    result = _deduplicate(detections)
    assert len(result) == 2
    names = {d.common_name for d in result}
    assert names == {"Barred Owl", "Rock Pigeon"}
    owl = next(d for d in result if d.common_name == "Barred Owl")
    assert owl.confidence == 0.94


def test_deduplicate_empty() -> None:
    assert _deduplicate([]) == []


def test_deduplicate_single() -> None:
    det = Detection("Blue Jay", "Cyanocitta cristata", 0.85, datetime(2026, 4, 6, 12, 0))
    result = _deduplicate([det])
    assert result == [det]
