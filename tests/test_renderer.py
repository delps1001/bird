from __future__ import annotations

from pathlib import Path

from bird_listener.display.renderer import PillowRenderer
from bird_listener.persistence.models import BirdSummary

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "birds"
OUTPUT_DIR = Path(__file__).parent / "output"


def _sample_birds(n: int = 3) -> list[BirdSummary]:
    data = [
        BirdSummary("Bald Eagle", "Haliaeetus leucocephalus", 1, 1, 0.92),
        BirdSummary("Blue Jay", "Cyanocitta cristata", 5, 2, 0.88),
        BirdSummary("House Finch", "Haemorhous mexicanus", 50, 10, 0.95),
    ]
    return data[:n]


def test_render_dimensions() -> None:
    renderer = PillowRenderer()
    img = renderer.render(_sample_birds(), ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)


def test_render_empty_state() -> None:
    renderer = PillowRenderer()
    img = renderer.render([], ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)
    # Should not be entirely white (has "no birds" text)
    pixels = list(img.getdata())
    assert not all(p == (255, 255, 255) for p in pixels)


def test_render_single_bird() -> None:
    renderer = PillowRenderer()
    img = renderer.render(_sample_birds(1), ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)


def test_hero_region_has_content() -> None:
    renderer = PillowRenderer()
    img = renderer.render(_sample_birds(), ASSETS_DIR, 800, 480)
    # Hero is top 65% = 312 pixels. Crop hero and check it's not blank.
    hero = img.crop((0, 0, 800, 312))
    hero_pixels = list(hero.getdata())
    assert not all(p == (255, 255, 255) for p in hero_pixels)


def test_secondary_has_content_with_3_birds() -> None:
    renderer = PillowRenderer()
    img = renderer.render(_sample_birds(3), ASSETS_DIR, 800, 480)
    # Secondary is bottom 35% = 168 pixels
    secondary = img.crop((0, 312, 800, 480))
    sec_pixels = list(secondary.getdata())
    assert not all(p == (255, 255, 255) for p in sec_pixels)


def test_multi_resolution_consistency() -> None:
    renderer = PillowRenderer()
    birds = _sample_birds()

    img_small = renderer.render(birds, ASSETS_DIR, 400, 300)
    img_large = renderer.render(birds, ASSETS_DIR, 800, 600)

    assert img_small.size == (400, 300)
    assert img_large.size == (800, 600)

    # Both should have non-blank hero regions (top 65%)
    for img, h in [(img_small, 300), (img_large, 600)]:
        hero_h = round(0.65 * h)
        hero = img.crop((0, 0, img.width, hero_h))
        assert not all(p == (255, 255, 255) for p in hero.getdata())


def test_render_saves_pngs_for_inspection() -> None:
    """Generate PNGs at multiple resolutions for visual inspection."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    renderer = PillowRenderer()
    birds = _sample_birds()

    for w, h in [(400, 300), (800, 480), (1200, 825)]:
        img = renderer.render(birds, ASSETS_DIR, w, h)
        img.save(OUTPUT_DIR / f"render_{w}x{h}.png")

    # Also render empty state
    img = renderer.render([], ASSETS_DIR, 800, 480)
    img.save(OUTPUT_DIR / "render_empty.png")
