from __future__ import annotations

from pathlib import Path

from bird_listener.display.fieldguide_renderer import FieldGuideRenderer
from bird_listener.persistence.models import BirdSummary

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "birds"


def _bird(name: str, count: int, *, is_new: bool = False) -> BirdSummary:
    return BirdSummary(
        common_name=name,
        scientific_name=f"{name.split()[0].lower()} sp.",
        lifetime_count=count,
        recent_count=1,
        best_confidence=0.9,
        is_new=is_new,
    )


def test_render_marks_new_birds_with_star_differently_than_count() -> None:
    """A new bird (star) should produce a different pixel pattern in the
    region where '<count>x' would otherwise be drawn."""
    renderer = FieldGuideRenderer()

    new_birds = [
        _bird("Bald Eagle", 1, is_new=True),
        _bird("Blue Jay", 5, is_new=True),
        _bird("House Finch", 50, is_new=True),
    ]
    old_birds = [_bird(b.common_name, b.lifetime_count) for b in new_birds]

    img_new = renderer.render(new_birds, ASSETS_DIR, 800, 480)
    img_old = renderer.render(old_birds, ASSETS_DIR, 800, 480)

    # If the count column changed (number → star), the images must differ.
    assert list(img_new.getdata()) != list(img_old.getdata())


def test_render_handles_mix_of_new_and_old_birds() -> None:
    renderer = FieldGuideRenderer()
    birds = [
        _bird("Bald Eagle", 1, is_new=True),
        _bird("Blue Jay", 12),
        _bird("House Finch", 50),
    ]
    img = renderer.render(birds, ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)
