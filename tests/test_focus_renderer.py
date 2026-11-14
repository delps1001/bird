from __future__ import annotations

from pathlib import Path

from bird_listener.display.focus_renderer import FocusRenderer
from bird_listener.persistence.models import BirdSummary

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "birds"


def _bird(name: str, count: int, *, is_new: bool = False) -> BirdSummary:
    return BirdSummary(
        common_name=name, scientific_name="x y", lifetime_count=count,
        recent_count=2, best_confidence=0.9, is_new=is_new,
    )


def test_max_birds_is_one() -> None:
    assert FocusRenderer().max_birds == 1


def test_renders_requested_size() -> None:
    img = FocusRenderer(inset=0.07).render([_bird("Bald Eagle", 1)], ASSETS_DIR, 480, 800)
    assert img.size == (480, 800)


def test_only_first_bird_is_shown() -> None:
    r = FocusRenderer()
    one = r.render([_bird("Bald Eagle", 1)], ASSETS_DIR, 800, 480)
    many = r.render([_bird("Bald Eagle", 1), _bird("Blue Jay", 9)], ASSETS_DIR, 800, 480)
    assert list(one.getdata()) == list(many.getdata())


def test_new_bird_differs_and_empty_renders() -> None:
    r = FocusRenderer()
    a = r.render([_bird("Bald Eagle", 1, is_new=True)], ASSETS_DIR, 800, 480)
    b = r.render([_bird("Bald Eagle", 1)], ASSETS_DIR, 800, 480)
    assert list(a.getdata()) != list(b.getdata())
    assert r.render([], ASSETS_DIR, 800, 480).size == (800, 480)
