"""Tests for draw_bird_card."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from bird_listener.display.bird_card import (
    HERO_STYLE,
    SECONDARY_STYLE,
    draw_bird_card,
)
from bird_listener.persistence.models import BirdSummary

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "birds"


def _make_bird(name: str = "Blue Jay") -> BirdSummary:
    return BirdSummary(name, "Cyanocitta cristata", 5, 2, 0.88)


def test_card_draws_content_in_region() -> None:
    canvas = Image.new("RGB", (400, 300), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    draw_bird_card(canvas, draw, _make_bird(), ASSETS_DIR, 50, 50, 200, 200, HERO_STYLE)

    # The region should have non-white pixels
    region = canvas.crop((50, 50, 250, 250))
    pixels = list(region.getdata())
    assert not all(p == (255, 255, 255) for p in pixels)


def test_custom_info_format() -> None:
    canvas = Image.new("RGB", (400, 300), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    draw_bird_card(
        canvas, draw, _make_bird(), ASSETS_DIR,
        0, 0, 400, 300, HERO_STYLE,
        info_format="Seen {lifetime_count} times",
    )

    # Should produce non-blank output
    pixels = list(canvas.getdata())
    assert not all(p == (255, 255, 255) for p in pixels)


def test_fallback_image() -> None:
    """Card for unknown species should still draw (using fallback)."""
    canvas = Image.new("RGB", (400, 300), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    bird = BirdSummary("Unknown Bird XYZ", "Unknown sp.", 1, 1, 0.5)
    draw_bird_card(canvas, draw, bird, ASSETS_DIR, 0, 0, 400, 300, SECONDARY_STYLE)

    pixels = list(canvas.getdata())
    assert not all(p == (255, 255, 255) for p in pixels)


def test_style_differences() -> None:
    """Hero and secondary styles should produce different results."""
    bird = _make_bird()

    canvas_hero = Image.new("RGB", (300, 300), (255, 255, 255))
    draw_bird_card(canvas_hero, ImageDraw.Draw(canvas_hero), bird, ASSETS_DIR,
                   0, 0, 300, 300, HERO_STYLE)

    canvas_sec = Image.new("RGB", (300, 300), (255, 255, 255))
    draw_bird_card(canvas_sec, ImageDraw.Draw(canvas_sec), bird, ASSETS_DIR,
                   0, 0, 300, 300, SECONDARY_STYLE)

    # Images should differ because of different font sizes and image area
    assert list(canvas_hero.getdata()) != list(canvas_sec.getdata())


def test_zero_size_does_not_crash() -> None:
    canvas = Image.new("RGB", (100, 100), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    draw_bird_card(canvas, draw, _make_bird(), ASSETS_DIR, 0, 0, 0, 0, HERO_STYLE)
    # Should not raise


def test_text_stays_within_card_bounds() -> None:
    """Text must not overflow any edge of the card rect, even for long names in narrow cells."""
    long_names = [
        "Red-bellied Woodpecker",
        "Northern Rough-winged Swallow",
        "Brown-headed Nuthatch",
        "Yellow-rumped Warbler",
    ]
    margin = 2  # allow for anti-aliasing

    for name in long_names:
        bird = BirdSummary(name, "Sci name", 5, 2, 0.88)
        # Narrow cell like a side column
        card_x, card_y, card_w, card_h = 200, 100, 170, 150
        canvas = Image.new("RGB", (800, 480), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        draw_bird_card(canvas, draw, bird, ASSETS_DIR,
                       card_x, card_y, card_w, card_h, SECONDARY_STYLE)

        # Check all four sides outside the card are white
        above = canvas.crop((0, 0, 800, card_y - margin))
        assert all(p == (255, 255, 255) for p in above.getdata()), \
            f"'{name}' leaked above card"
        below = canvas.crop((0, card_y + card_h + margin, 800, 480))
        assert all(p == (255, 255, 255) for p in below.getdata()), \
            f"'{name}' leaked below card"
        left = canvas.crop((0, 0, card_x - margin, 480))
        assert all(p == (255, 255, 255) for p in left.getdata()), \
            f"'{name}' leaked left of card"
        right = canvas.crop((card_x + card_w + margin, 0, 800, 480))
        assert all(p == (255, 255, 255) for p in right.getdata()), \
            f"'{name}' leaked right of card"


def test_long_name_in_narrow_cell() -> None:
    """Even extremely long names must not extend beyond a narrow cell."""
    bird = BirdSummary("Northern Rough-winged Swallow", "Sci name", 1, 1, 0.9)
    card_x, card_y, card_w, card_h = 100, 50, 120, 140
    canvas = Image.new("RGB", (400, 300), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    draw_bird_card(canvas, draw, bird, ASSETS_DIR,
                   card_x, card_y, card_w, card_h, SECONDARY_STYLE)

    margin = 2
    right = canvas.crop((card_x + card_w + margin, 0, 400, 300))
    assert all(p == (255, 255, 255) for p in right.getdata()), \
        "Long name overflowed right edge"
    left = canvas.crop((0, 0, card_x - margin, 300))
    assert all(p == (255, 255, 255) for p in left.getdata()), \
        "Long name overflowed left edge"


def test_scales_across_resolutions() -> None:
    """Same card drawn at different sizes should produce proportional results."""
    bird = _make_bird()

    # Small cell
    small = Image.new("RGB", (200, 150), (255, 255, 255))
    draw_bird_card(small, ImageDraw.Draw(small), bird, ASSETS_DIR,
                   0, 0, 200, 150, HERO_STYLE)

    # Large cell
    large = Image.new("RGB", (600, 450), (255, 255, 255))
    draw_bird_card(large, ImageDraw.Draw(large), bird, ASSETS_DIR,
                   0, 0, 600, 450, HERO_STYLE)

    # Both should have non-white content
    assert not all(p == (255, 255, 255) for p in small.getdata())
    assert not all(p == (255, 255, 255) for p in large.getdata())
