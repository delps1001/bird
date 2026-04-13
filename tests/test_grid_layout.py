"""Tests for GridDisplayLayout geometry."""
from __future__ import annotations

from bird_listener.display.grid_layout import DEFAULT_GRID_LAYOUT, GridDisplayLayout
from bird_listener.display.layout import resolve


def test_cell_count() -> None:
    layout = DEFAULT_GRID_LAYOUT
    cells = layout.cell_regions()
    assert len(cells) == 6


def test_no_overlap() -> None:
    layout = DEFAULT_GRID_LAYOUT
    cells = layout.cell_regions()
    width, height = 800, 480

    rects = [resolve(c, width, height) for c in cells]

    for i, (x1, y1, w1, h1) in enumerate(rects):
        for j, (x2, y2, w2, h2) in enumerate(rects):
            if i >= j:
                continue
            # Check that rectangles don't overlap (allow 1px rounding tolerance)
            no_overlap = (
                x1 + w1 <= x2 + 1
                or x2 + w2 <= x1 + 1
                or y1 + h1 <= y2 + 1
                or y2 + h2 <= y1 + 1
            )
            assert no_overlap, f"Cells {i} and {j} overlap: ({x1},{y1},{w1},{h1}) vs ({x2},{y2},{w2},{h2})"


def test_footer_below_grid() -> None:
    layout = DEFAULT_GRID_LAYOUT
    cells = layout.cell_regions()
    footer = layout.footer_region()
    width, height = 800, 480

    # Footer y should be >= bottom of all grid cells
    fx, fy, fw, fh = resolve(footer, width, height)
    for cell in cells:
        cx, cy, cw, ch = resolve(cell, width, height)
        assert fy >= cy + ch - 1, "Footer overlaps with grid cell"


def test_inset_shrinks_usable_area() -> None:
    layout_small = GridDisplayLayout(inset=0.02)
    layout_large = GridDisplayLayout(inset=0.10)
    width, height = 800, 480

    cells_small = layout_small.cell_regions()
    cells_large = layout_large.cell_regions()

    # Cells with larger inset should be smaller
    _, _, w_small, h_small = resolve(cells_small[0], width, height)
    _, _, w_large, h_large = resolve(cells_large[0], width, height)

    assert w_large < w_small
    assert h_large < h_small


def test_zero_inset() -> None:
    layout = GridDisplayLayout(inset=0.0)
    cells = layout.cell_regions()
    footer = layout.footer_region()
    width, height = 800, 480

    # With zero inset, hero should start at 0,0
    hx, hy, _, _ = resolve(cells[0], width, height)  # rank 0 = hero
    assert hy == 0

    # Footer should extend to bottom
    fx, fy, fw, fh = resolve(footer, width, height)
    assert fy + fh == height or abs((fy + fh) - height) <= 1


def test_hero_is_top_center() -> None:
    layout = DEFAULT_GRID_LAYOUT
    cells = layout.cell_regions()
    width, height = 800, 480

    hero = cells[0]  # rank 0 = hero
    top_left = cells[1]  # rank 1 = top-left

    hx, hy, hw, hh = resolve(hero, width, height)
    tlx, tly, tlw, tlh = resolve(top_left, width, height)

    # Hero should be to the right of top-left
    assert hx > tlx
    # Hero should start at or above the top-left bird (side birds are centred)
    assert hy <= tly
    # Hero should be significantly larger than secondary
    assert hw > tlw
    assert hh > tlh
