"""Tests for GridRenderer and PicolayGridRenderer.

Every behavioural test is parametrized to run against both implementations,
proving the picolay version is a drop-in replacement.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from bird_listener.display.grid_layout import GridDisplayLayout
from bird_listener.display.grid_renderer import GridRenderer
from bird_listener.display.grid_renderer_picolay import PicolayGridRenderer
from bird_listener.persistence.models import BirdSummary

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "birds"
OUTPUT_DIR = Path(__file__).parent / "output"


def _sample_birds(n: int = 6) -> list[BirdSummary]:
    data = [
        BirdSummary("Bald Eagle", "Haliaeetus leucocephalus", 1, 1, 0.92,
                     datetime(2026, 4, 12, 15, 42)),
        BirdSummary("Blue Jay", "Cyanocitta cristata", 5, 2, 0.88,
                     datetime(2026, 4, 12, 14, 30)),
        BirdSummary("House Finch", "Haemorhous mexicanus", 50, 10, 0.95,
                     datetime(2026, 4, 12, 13, 15)),
        BirdSummary("Cardinal", "Cardinalis cardinalis", 20, 3, 0.91,
                     datetime(2026, 4, 12, 12, 0)),
        BirdSummary("Robin", "Turdus migratorius", 30, 5, 0.87,
                     datetime(2026, 4, 12, 11, 0)),
        BirdSummary("Sparrow", "Passer domesticus", 100, 15, 0.93,
                     datetime(2026, 4, 12, 10, 0)),
    ]
    return data[:n]


# ---------------------------------------------------------------------------
# Fixture: parametrize over both renderer implementations
# ---------------------------------------------------------------------------

def _make_grid(layout=None):
    return GridRenderer(layout=layout)


def _make_picolay(layout=None):
    return PicolayGridRenderer(layout=layout)


@pytest.fixture(params=[_make_grid, _make_picolay], ids=["GridRenderer", "PicolayGridRenderer"])
def renderer_factory(request):
    """Returns a callable(layout=None) -> renderer."""
    return request.param


# ---------------------------------------------------------------------------
# Behavioural tests — run against both renderers
# ---------------------------------------------------------------------------

def test_render_dimensions(renderer_factory) -> None:
    renderer = renderer_factory()
    img = renderer.render(_sample_birds(), ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)


def test_render_empty_state(renderer_factory) -> None:
    renderer = renderer_factory()
    img = renderer.render([], ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)
    pixels = list(img.getdata())
    assert not all(p == (255, 255, 255) for p in pixels)


def test_render_single_bird(renderer_factory) -> None:
    renderer = renderer_factory()
    img = renderer.render(_sample_birds(1), ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)
    pixels = list(img.getdata())
    assert not all(p == (255, 255, 255) for p in pixels)


def test_no_content_outside_cells(renderer_factory) -> None:
    """Text from one cell must not bleed into adjacent cells' territory."""
    long_name_birds = [
        BirdSummary("Cedar Waxwing", "B c", 1, 1, 0.92,
                     datetime(2026, 4, 12, 15, 0)),
        BirdSummary("Red-bellied Woodpecker", "M c", 2, 2, 0.88,
                     datetime(2026, 4, 12, 14, 0)),
        BirdSummary("Northern Rough-winged Swallow", "S s", 3, 3, 0.85,
                     datetime(2026, 4, 12, 13, 0)),
        BirdSummary("Yellow-rumped Warbler", "S c", 4, 4, 0.90,
                     datetime(2026, 4, 12, 12, 0)),
        BirdSummary("Brown-headed Nuthatch", "S p", 5, 5, 0.87,
                     datetime(2026, 4, 12, 11, 0)),
        BirdSummary("Black-and-white Warbler", "M v", 6, 6, 0.93,
                     datetime(2026, 4, 12, 10, 0)),
    ]
    renderer = renderer_factory()
    w, h = 800, 480
    img = renderer.render(long_name_birds, ASSETS_DIR, w, h)

    layout = GridDisplayLayout()
    inset = round(layout.inset * w)
    margin = 2
    left = img.crop((0, 0, inset - margin, h))
    assert all(p == (255, 255, 255) for p in left.getdata()), \
        "Content leaked into left inset"
    right = img.crop((w - inset + margin, 0, w, h))
    assert all(p == (255, 255, 255) for p in right.getdata()), \
        "Content leaked into right inset"


def test_all_six_cells_filled(renderer_factory) -> None:
    renderer = renderer_factory()
    img = renderer.render(_sample_birds(6), ASSETS_DIR, 800, 480)

    layout = GridDisplayLayout()
    from bird_listener.display.layout import resolve

    cells = layout.cell_regions()
    for i, cell in enumerate(cells):
        x, y, w, h = resolve(cell, 800, 480)
        region = img.crop((x, y, x + w, y + h))
        pixels = list(region.getdata())
        assert not all(p == (255, 255, 255) for p in pixels), f"Cell {i} is blank"


def test_fewer_than_six(renderer_factory) -> None:
    renderer = renderer_factory()
    img = renderer.render(_sample_birds(3), ASSETS_DIR, 800, 480)
    assert img.size == (800, 480)

    layout = GridDisplayLayout()
    from bird_listener.display.layout import resolve

    cells = layout.cell_regions()
    for i in range(3):
        x, y, w, h = resolve(cells[i], 800, 480)
        region = img.crop((x, y, x + w, y + h))
        pixels = list(region.getdata())
        assert not all(p == (255, 255, 255) for p in pixels), f"Cell {i} is blank"


def test_footer_with_detection(renderer_factory) -> None:
    layout = GridDisplayLayout(grid_height_frac=0.88, footer_height_frac=0.12)
    renderer = renderer_factory(layout=layout)
    birds = _sample_birds(2)
    img = renderer.render(birds, ASSETS_DIR, 800, 480)

    from bird_listener.display.layout import resolve

    fx, fy, fw, fh = resolve(layout.footer_region(), 800, 480)
    footer = img.crop((fx, fy, fx + fw, fy + fh))
    pixels = list(footer.getdata())
    assert not all(p == (255, 255, 255) for p in pixels)


def test_footer_without_detection(renderer_factory) -> None:
    """Birds with no last_detected_at should produce a blank footer."""
    layout = GridDisplayLayout(grid_height_frac=0.88, footer_height_frac=0.12)
    renderer = renderer_factory(layout=layout)
    birds = [BirdSummary("Finch", "F f", 10, 3, 0.9)]
    img = renderer.render(birds, ASSETS_DIR, 800, 480)

    from bird_listener.display.layout import resolve

    fx, fy, fw, fh = resolve(layout.footer_region(), 800, 480)
    footer = img.crop((fx, fy, fx + fw, fy + fh))
    pixels = list(footer.getdata())
    assert all(p == (255, 255, 255) for p in pixels)


def test_footer_hidden_by_default(renderer_factory) -> None:
    """Default layout has no footer — all space goes to the grid."""
    renderer = renderer_factory()
    birds = _sample_birds(6)
    renderer.render(birds, ASSETS_DIR, 800, 480)

    layout = GridDisplayLayout()
    assert layout.footer_height_frac == 0.0


def test_inset_white_border(renderer_factory) -> None:
    """With a large inset, all four border strips should be white."""
    inset_frac = 0.10
    layout = GridDisplayLayout(inset=inset_frac)
    renderer = renderer_factory(layout=layout)
    w, h = 800, 480
    img = renderer.render(_sample_birds(6), ASSETS_DIR, w, h)

    inset_x = round(inset_frac * w) - 2
    inset_y = round(inset_frac * h) - 2

    top = img.crop((0, 0, w, inset_y))
    assert all(p == (255, 255, 255) for p in top.getdata()), "Top inset border is not white"

    bottom = img.crop((0, h - inset_y, w, h))
    assert all(p == (255, 255, 255) for p in bottom.getdata()), "Bottom inset border is not white"

    left = img.crop((0, 0, inset_x, h))
    assert all(p == (255, 255, 255) for p in left.getdata()), "Left inset border is not white"

    right = img.crop((w - inset_x, 0, w, h))
    assert all(p == (255, 255, 255) for p in right.getdata()), "Right inset border is not white"


def test_inset_pushes_content_inward(renderer_factory) -> None:
    """Content should only appear inside the inset boundary."""
    inset_frac = 0.15
    layout = GridDisplayLayout(inset=inset_frac)
    renderer = renderer_factory(layout=layout)
    w, h = 800, 480
    img = renderer.render(_sample_birds(6), ASSETS_DIR, w, h)

    inset_x = round(inset_frac * w)
    inset_y = round(inset_frac * h)

    interior = img.crop((inset_x, inset_y, w - inset_x, h - inset_y))
    assert not all(p == (255, 255, 255) for p in interior.getdata()), "Interior has no content"


def test_extreme_inset_no_overflow(renderer_factory) -> None:
    """At 0.3 inset, content must stay within the inset boundary and not overlap."""
    inset_frac = 0.30
    layout = GridDisplayLayout(inset=inset_frac)
    renderer = renderer_factory(layout=layout)
    w, h = 800, 480
    img = renderer.render(_sample_birds(6), ASSETS_DIR, w, h)

    inset_x = round(inset_frac * w)
    inset_y = round(inset_frac * h)

    margin = 2
    top = img.crop((0, 0, w, inset_y - margin))
    assert all(p == (255, 255, 255) for p in top.getdata()), "Content leaked into top inset"
    bottom = img.crop((0, h - inset_y + margin, w, h))
    assert all(p == (255, 255, 255) for p in bottom.getdata()), "Content leaked into bottom inset"
    left = img.crop((0, 0, inset_x - margin, h))
    assert all(p == (255, 255, 255) for p in left.getdata()), "Content leaked into left inset"
    right = img.crop((w - inset_x + margin, 0, w, h))
    assert all(p == (255, 255, 255) for p in right.getdata()), "Content leaked into right inset"

    interior = img.crop((inset_x, inset_y, w - inset_x, h - inset_y))
    assert not all(p == (255, 255, 255) for p in interior.getdata()), "Interior is blank"


def test_extreme_inset_at_multiple_resolutions(renderer_factory) -> None:
    """Large inset should work correctly at various display sizes."""
    layout = GridDisplayLayout(inset=0.25)
    renderer = renderer_factory(layout=layout)
    birds = _sample_birds(6)

    for w, h in [(400, 300), (800, 480), (1200, 825)]:
        img = renderer.render(birds, ASSETS_DIR, w, h)
        assert img.size == (w, h)
        inset_x = round(0.25 * w) - 2
        inset_y = round(0.25 * h) - 2
        top = img.crop((0, 0, w, inset_y))
        assert all(p == (255, 255, 255) for p in top.getdata()), \
            f"Content leaked at {w}x{h}"
        interior = img.crop((inset_x + 4, inset_y + 4, w - inset_x - 4, h - inset_y - 4))
        assert not all(p == (255, 255, 255) for p in interior.getdata()), \
            f"Interior blank at {w}x{h}"


def test_multi_resolution(renderer_factory) -> None:
    renderer = renderer_factory()
    birds = _sample_birds()

    for w, h in [(400, 300), (800, 480), (1200, 825)]:
        img = renderer.render(birds, ASSETS_DIR, w, h)
        assert img.size == (w, h)


# ---------------------------------------------------------------------------
# Tests that only apply to one implementation
# ---------------------------------------------------------------------------

def test_satisfies_display_renderer_protocol() -> None:
    from bird_listener.ports import DisplayRenderer

    assert isinstance(GridRenderer(), DisplayRenderer)
    assert isinstance(PicolayGridRenderer(), DisplayRenderer)


def test_render_saves_pngs_for_inspection() -> None:
    """Generate grid PNGs for visual inspection from both renderers."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    birds = _sample_birds()

    for prefix, factory in [("grid", _make_grid), ("picolay_grid", _make_picolay)]:
        renderer = factory()

        for w, h in [(400, 300), (800, 480), (1200, 825)]:
            img = renderer.render(birds, ASSETS_DIR, w, h)
            img.save(OUTPUT_DIR / f"{prefix}_{w}x{h}.png")

        # Empty state
        img = renderer.render([], ASSETS_DIR, 800, 480)
        img.save(OUTPUT_DIR / f"{prefix}_empty.png")

        # Single bird
        img = renderer.render(_sample_birds(1), ASSETS_DIR, 800, 480)
        img.save(OUTPUT_DIR / f"{prefix}_single.png")

        # Large inset
        layout = GridDisplayLayout(inset=0.10)
        renderer_inset = factory(layout=layout)
        img = renderer_inset.render(birds, ASSETS_DIR, 800, 480)
        img.save(OUTPUT_DIR / f"{prefix}_inset10.png")

        # Extreme inset
        layout = GridDisplayLayout(inset=0.30)
        renderer_inset = factory(layout=layout)
        img = renderer_inset.render(birds, ASSETS_DIR, 800, 480)
        img.save(OUTPUT_DIR / f"{prefix}_inset30.png")
