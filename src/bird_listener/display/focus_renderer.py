"""Focus renderer: a single bird, vertically stacked and centered.

Shows only the top-ranked bird (new species first, otherwise the rarest in
the recent window): large pixel-art image, then common name, scientific
name, and a stats line. Newly-recognized species get a "NEW" badge.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

_MIN_FONT = 6
_BG = (255, 255, 255)
_DARK = (40, 40, 40)
_MUTED = (130, 130, 130)
_ACCENT = (235, 87, 87)


class FocusRenderer:
    """Single-bird vertical layout showing only the rarest recent bird."""

    def __init__(self, inset: float = 0.0):
        self._inset = inset

    @property
    def max_birds(self) -> int:
        return 1

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        inset_x = round(self._inset * width)
        inset_y = round(self._inset * height)
        pad = max(4, min(width, height) // 50)
        padding = (pad + inset_y, pad + inset_x, pad + inset_y, pad + inset_x)
        usable_w = width - padding[1] - padding[3]
        usable_h = height - padding[0] - padding[2]

        if not birds:
            tree = Box(
                style=Style(
                    width=width, height=height, background=_BG, padding=padding,
                    flex_direction="column", align_items="center",
                    justify_content="center",
                ),
                children=[
                    Text("Listening...", style=Style(
                        font_size=max(_MIN_FONT, height // 16), font_color=_MUTED)),
                ],
            )
            return render(tree, width, height, background=_BG)

        bird = birds[0]
        img_h = round(usable_h * 0.62)
        text_h = usable_h - img_h
        name_sz = max(_MIN_FONT, min(text_h * 2 // 5, usable_w // 10))
        sci_sz = max(_MIN_FONT, name_sz * 2 // 3)
        stat_sz = max(_MIN_FONT, name_sz // 2)

        if bird.is_new:
            stats = f"NEW SPECIES · {bird.recent_count} today"
            stat_color = _ACCENT
        else:
            stats = f"Seen {bird.lifetime_count}x lifetime · {bird.recent_count} today"
            stat_color = _MUTED

        root = Box(
            style=Style(
                width=width, height=height, background=_BG, padding=padding,
                flex_direction="column", align_items="center",
            ),
            children=[
                Img(
                    src=load_bird_image(bird.common_name, assets_dir),
                    style=Style(
                        width=usable_w, height=img_h,
                        object_fit="contain", image_rendering="pixelated",
                    ),
                ),
                Box(
                    style=Style(
                        width=usable_w, height=text_h, flex_direction="column",
                        align_items="center", justify_content="center",
                        overflow="hidden",
                    ),
                    children=[
                        Text(bird.common_name, style=Style(
                            font_size=name_sz, font_color=_DARK,
                            text_align="center", font_shrink=True)),
                        Text(bird.scientific_name, style=Style(
                            font_size=sci_sz, font_color=_MUTED,
                            text_align="center", font_shrink=True)),
                        Text(stats, style=Style(
                            font_size=stat_sz, font_color=stat_color,
                            text_align="center", font_shrink=True)),
                    ],
                ),
            ],
        )
        return render(root, width, height, background=_BG)
