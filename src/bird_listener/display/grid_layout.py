"""Grid layout definition for e-ink display with hero-prominent arrangement.

The hero bird occupies a large center region in the top section. The five
secondary birds are all the same size: two flanking the hero (vertically
centred) and three in a bottom row.

    ┌──────┬──────────────┬──────┐
    │      │              │      │
    │ 2nd  │    HERO      │ 6th  │  top section (65%)
    │      │              │      │
    ├──────┼────┬────┬────┼──────┤
    │  3rd │ 4th│    │5th │      │  bottom section (35%)
    └──────┴────┴────┴────┴──────┘
"""
from __future__ import annotations

from dataclasses import dataclass

from bird_listener.display.layout import LayoutRegion

# Proportions (fractions of usable width / grid height)
_SIDE_W = 0.22          # width of each side column
_CENTER_W = 1.0 - 2 * _SIDE_W  # width of center column
_TOP_H = 0.65           # top section height (hero)
_BOT_H = 1.0 - _TOP_H  # bottom section height


@dataclass(frozen=True)
class GridDisplayLayout:
    """Layout parameters for a grid display with footer and inset."""

    inset: float = 0.02  # uniform fraction for e-ink frame cropping
    grid_height_frac: float = 1.0  # fraction of usable area for the grid
    footer_height_frac: float = 0.0  # fraction of usable area for footer (0 = hidden)
    hero_image_area: float = 0.70
    secondary_image_area: float = 0.60

    def cell_regions(self) -> list[LayoutRegion]:
        """Return 6 LayoutRegions in rank order.

        All fractions are relative to the full canvas (inset applied).
        The hero dominates the center; all 5 secondaries share the same
        height so no bird appears larger than another.

        Rank order: hero, 2nd (top-left), 3rd (bottom-left),
                    4th (bottom-center), 5th (bottom-right), 6th (top-right).
        """
        ux = self.inset
        uy = self.inset
        uw = 1.0 - 2 * self.inset
        uh = 1.0 - 2 * self.inset
        gh = uh * self.grid_height_frac  # total grid height

        top_h = gh * _TOP_H
        bot_h = gh * _BOT_H
        side_w = uw * _SIDE_W
        center_w = uw * _CENTER_W

        # Side birds are vertically centred in the top section at bot_h height
        side_h = bot_h
        side_y_offset = (top_h - side_h) / 2

        # rank 0 — Hero (full top-center)
        hero = LayoutRegion(
            x_frac=ux + side_w,
            y_frac=uy,
            w_frac=center_w,
            h_frac=top_h,
        )
        # rank 1 — 2nd (top-left, centred vertically)
        second = LayoutRegion(
            x_frac=ux,
            y_frac=uy + side_y_offset,
            w_frac=side_w,
            h_frac=side_h,
        )
        # rank 5 — 6th (top-right, centred vertically)
        sixth = LayoutRegion(
            x_frac=ux + side_w + center_w,
            y_frac=uy + side_y_offset,
            w_frac=side_w,
            h_frac=side_h,
        )
        # Bottom row — same column widths as top (side | center | side)
        bot_y = uy + top_h
        third = LayoutRegion(x_frac=ux, y_frac=bot_y, w_frac=side_w, h_frac=bot_h)
        fourth = LayoutRegion(x_frac=ux + side_w, y_frac=bot_y, w_frac=center_w, h_frac=bot_h)
        fifth = LayoutRegion(x_frac=ux + side_w + center_w, y_frac=bot_y, w_frac=side_w, h_frac=bot_h)

        return [hero, second, third, fourth, fifth, sixth]

    def footer_region(self) -> LayoutRegion:
        """Return the footer LayoutRegion below the grid."""
        usable_x = self.inset
        usable_y = self.inset
        usable_w = 1.0 - 2 * self.inset
        usable_h = 1.0 - 2 * self.inset

        grid_h = usable_h * self.grid_height_frac
        footer_y = usable_y + grid_h
        footer_h = usable_h * self.footer_height_frac

        return LayoutRegion(
            x_frac=usable_x,
            y_frac=footer_y,
            w_frac=usable_w,
            h_frac=footer_h,
        )


DEFAULT_GRID_LAYOUT = GridDisplayLayout()
