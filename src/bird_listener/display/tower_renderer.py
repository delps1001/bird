"""Tower renderer: a single vertical column of stacked bird cards.

Visual concept: A totem pole / apartment building of birds. Each bird gets
a horizontal "floor" spanning the full width, stacked top to bottom. The #1
bird is at the top with the most vertical space and a colored accent
background. Lower-ranked birds get progressively thinner slices. A gradient
of warm-to-cool accent colors suggests a heatmap of popularity. Clean,
minimal, and instantly readable — great for narrow portrait e-ink panels.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

_MIN_FONT = 6
_BG = (255, 255, 255)

# Warm-to-cool gradient for ranks 1-6
_RANK_ACCENTS = [
    (235, 87, 87),    # 1: warm red
    (240, 150, 60),   # 2: orange
    (230, 195, 50),   # 3: gold
    (90, 185, 120),   # 4: green
    (70, 150, 200),   # 5: blue
    (140, 120, 190),  # 6: violet
]
_WHITE = (255, 255, 255)
_DARK = (40, 40, 40)
_MUTED = (130, 130, 130)



def _floor_card(
    bird: BirdSummary, assets_dir: Path,
    w: int, h: int, rank: int,
) -> Box:
    """One horizontal 'floor': accent bar | image | name | stats."""
    accent = _RANK_ACCENTS[(rank - 1) % len(_RANK_ACCENTS)]
    bird_img = load_bird_image(bird.common_name, assets_dir)

    accent_w = max(4, w // 40)
    thumb_sz = min(max(16, h - 8), 64)
    rank_num_w = min(max(16, h // 2), w // 8)
    stats_w = min(max(36, w // 7), w // 5)
    name_w = max(40, w - accent_w - rank_num_w - thumb_sz - stats_w - 24)

    rank_font = min(max(_MIN_FONT, h * 2 // 3), rank_num_w)
    name_sz = max(_MIN_FONT, min(h // 2, w // 12))
    count_sz = max(_MIN_FONT, name_sz * 2 // 3)
    count_font = max(_MIN_FONT, min(h // 2, w // 10))

    return Box(
        style=Style(
            width=w, height=h,
            flex_direction="row", align_items="center", overflow="hidden",
        ),
        children=[
            # Colored accent bar
            Box(style=Style(width=accent_w, height=h, background=accent)),
            # Rank number
            Text(str(rank), style=Style(
                width=rank_num_w, font_size=rank_font,
                font_color=accent, text_align="center",
                padding=(0, 2, 0, 6), font_shrink=True,
            )),
            # Bird thumbnail
            Img(src=bird_img, style=Style(width=thumb_sz, height=thumb_sz, object_fit="contain", image_rendering="pixelated")),
            # Name
            Box(
                style=Style(
                    width=name_w, flex_direction="column", justify_content="center",
                    padding=(0, 0, 0, 8), overflow="hidden",
                ),
                children=[
                    Text(bird.common_name, style=Style(font_size=name_sz, font_color=_DARK, font_shrink=True)),
                    Text(bird.scientific_name, style=Style(
                        font_size=max(_MIN_FONT, count_sz - 1), font_color=_MUTED,
                        font_shrink=True,
                    )),
                ],
            ),
            # Stats column
            Box(
                style=Style(
                    width=stats_w, flex_direction="column",
                    align_items="end", justify_content="center",
                    padding=(0, 8, 0, 0), overflow="hidden",
                ),
                children=[
                    Text(f"{bird.lifetime_count}x", style=Style(
                        font_size=count_font, font_color=accent, text_align="right",
                        font_shrink=True,
                    )),
                    Text(f"{bird.recent_count} today", style=Style(
                        font_size=max(_MIN_FONT, count_font * 2 // 3), font_color=_MUTED, text_align="right",
                        font_shrink=True,
                    )),
                ],
            ),
        ],
    )


def _divider(w: int) -> Box:
    return Box(style=Style(width=w, height=1, background=(225, 225, 225)))


class TowerRenderer:
    """Vertical totem-pole layout — stacked horizontal cards, heatmap-colored."""

    def __init__(self, inset: float = 0.0):
        self._inset = inset

    @property
    def max_birds(self) -> int:
        return 6

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        inset_x = round(self._inset * width)
        inset_y = round(self._inset * height)

        if not birds:
            tree = Box(
                style=Style(width=width, height=height, background=_BG,
                            padding=(inset_y, inset_x, inset_y, inset_x),
                            flex_direction="column", align_items="center", justify_content="center"),
                children=[
                    Text("Listening...",
                         style=Style(font_size=max(_MIN_FONT, height // 16), font_color=_MUTED)),
                ],
            )
            return render(tree, width, height, background=_BG)

        display = birds[:6]
        n = len(display)
        pad = max(4, min(width, height) // 50)

        # Hero gets proportionally more vertical space
        # Weights: hero=3, others=2 each
        total_weight = 3 + max(0, n - 1) * 2
        divider_total = max(0, n - 1)
        usable_h = height - (pad + inset_y) * 2 - divider_total
        hero_h = round(usable_h * 3 / total_weight)
        other_h = round(usable_h * 2 / total_weight) if n > 1 else 0

        usable_w = width - (pad + inset_x) * 2

        children: list[Box | Text | Img] = []
        for i, bird in enumerate(display):
            if i > 0:
                children.append(_divider(usable_w))
            fh = hero_h if i == 0 else other_h
            children.append(_floor_card(bird, assets_dir, usable_w, fh, rank=i + 1))

        root = Box(
            style=Style(
                width=width, height=height, background=_BG,
                padding=(pad + inset_y, pad + inset_x, pad + inset_y, pad + inset_x),
                flex_direction="column",
            ),
            children=children,
        )
        return render(root, width, height, background=_BG)
