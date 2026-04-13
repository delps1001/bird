"""Magazine-style renderer: huge hero bird with editorial text overlay, sidebar list.

Visual concept: Nature magazine cover. The #1 bird dominates 2/3 of the frame
with a large pixel-art render. A bold species name is overlaid at the bottom
of the hero area on a dark scrim. A narrow sidebar on the right lists the
remaining birds as compact rows (thumbnail + name + count), separated by
thin divider lines. A colored accent bar runs along the top with a title.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

_MIN_FONT = 6
_ACCENT = (45, 85, 55)        # deep forest green
_ACCENT_LIGHT = (75, 140, 90)
_SCRIM = (30, 30, 30)
_WHITE = (255, 255, 255)
_LIGHT_BG = (245, 243, 238)   # warm off-white
_MUTED = (120, 115, 105)
_DARK = (35, 35, 30)



def _sidebar_row(bird: BirdSummary, assets_dir: Path, row_w: int, row_h: int, rank: int) -> Box:
    """One sidebar entry: rank badge + thumbnail + name + count."""
    bird_img = load_bird_image(bird.common_name, assets_dir)
    thumb_size = max(16, row_h - 8)

    name_size = max(_MIN_FONT, row_h // 3)
    count_text = f"{bird.lifetime_count}x"
    count_size = max(_MIN_FONT, row_h // 4)

    return Box(
        style=Style(
            width=row_w, height=row_h,
            flex_direction="row", align_items="center",
            gap=4, padding=(0, 6, 0, 6), overflow="hidden",
        ),
        children=[
            # Rank number
            Text(
                str(rank),
                style=Style(
                    width=thumb_size, font_size=max(_MIN_FONT, row_h // 3),
                    font_color=_ACCENT, text_align="center", font_shrink=True,
                ),
            ),
            # Bird thumbnail
            Img(src=bird_img, style=Style(width=thumb_size, height=thumb_size, object_fit="contain", image_rendering="pixelated")),
            # Name + count stacked
            Box(
                style=Style(flex_grow=1, flex_direction="column", justify_content="center", gap=1),
                children=[
                    Text(bird.common_name, style=Style(font_size=name_size, font_color=_DARK, font_shrink=True)),
                    Text(count_text, style=Style(font_size=count_size, font_color=_MUTED, font_shrink=True)),
                ],
            ),
        ],
    )


def _divider(w: int) -> Box:
    return Box(style=Style(width=w, height=1, background=(210, 208, 200)))


class MagazineRenderer:
    """Nature magazine cover layout — hero bird + ranked sidebar."""

    def __init__(self, inset: float = 0.0):
        self._inset = inset

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        inset_x = round(self._inset * width)
        inset_y = round(self._inset * height)
        usable_w = width - 2 * inset_x
        usable_h = height - 2 * inset_y

        if not birds:
            tree = Box(
                style=Style(width=width, height=height, background=_LIGHT_BG,
                            padding=(inset_y, inset_x, inset_y, inset_x),
                            flex_direction="column", align_items="center", justify_content="center"),
                children=[
                    Text("No birds detected yet",
                         style=Style(font_size=max(_MIN_FONT, usable_h // 20), font_color=_MUTED)),
                ],
            )
            return render(tree, width, height, background=_LIGHT_BG)

        display = birds[:6]
        hero_bird = display[0]

        # Layout proportions
        accent_h = max(6, usable_h // 18)
        hero_w = round(usable_w * 0.62)
        sidebar_w = usable_w - hero_w
        body_h = usable_h - accent_h

        # --- Accent bar ---
        title_size = max(_MIN_FONT, accent_h - 4)
        accent_bar = Box(
            style=Style(
                width=usable_w, height=accent_h, background=_ACCENT,
                flex_direction="row", align_items="center", padding=(0, 10, 0, 10),
            ),
            children=[
                Text("BIRD LISTENER", style=Style(font_size=title_size, font_color=_WHITE, font_shrink=True)),
            ],
        )

        # --- Hero section ---
        hero_img = load_bird_image(hero_bird.common_name, assets_dir)
        name_size = max(12, body_h // 8)

        scrim_h = max(30, body_h // 5)
        hero_image_h = body_h - scrim_h

        hero_section = Box(
            style=Style(width=hero_w, height=body_h, flex_direction="column", background=_LIGHT_BG),
            children=[
                # Large bird image
                Img(src=hero_img, style=Style(
                    width=hero_w, height=hero_image_h, object_fit="contain",
                    image_rendering="pixelated",
                )),
                # Dark scrim with name overlay
                Box(
                    style=Style(
                        width=hero_w, height=scrim_h, background=_SCRIM,
                        flex_direction="column", justify_content="center",
                        padding=(4, 12, 4, 12), overflow="hidden",
                    ),
                    children=[
                        Text(hero_bird.common_name, style=Style(
                            font_size=name_size, font_color=_WHITE, text_align="left",
                            font_shrink=True,
                        )),
                        Text(
                            f"{hero_bird.scientific_name}  |  {hero_bird.lifetime_count}x lifetime",
                            style=Style(
                                font_size=max(_MIN_FONT, name_size // 2),
                                font_color=_ACCENT_LIGHT, text_align="left",
                                font_shrink=True,
                            ),
                        ),
                    ],
                ),
            ],
        )

        # --- Sidebar ---
        sidebar_children: list[Box | Text | Img] = []
        # Sidebar header
        header_h = max(18, body_h // 14)
        sidebar_children.append(Box(
            style=Style(
                width=sidebar_w, height=header_h, background=_ACCENT,
                flex_direction="row", align_items="center", padding=(0, 8, 0, 8),
            ),
            children=[
                Text("RECENT SIGHTINGS", style=Style(
                    font_size=max(_MIN_FONT, header_h - 6), font_color=_WHITE,
                    font_shrink=True,
                )),
            ],
        ))

        # List rows
        remaining = display[1:]
        if remaining:
            row_h = min((body_h - header_h) // max(1, len(remaining)), body_h // 5)
            for i, bird in enumerate(remaining):
                if i > 0:
                    sidebar_children.append(_divider(sidebar_w))
                sidebar_children.append(
                    _sidebar_row(bird, assets_dir, sidebar_w, row_h, rank=i + 2)
                )

        sidebar = Box(
            style=Style(
                width=sidebar_w, height=body_h, flex_direction="column",
                background=_LIGHT_BG,
            ),
            children=sidebar_children,
        )

        # --- Assemble ---
        body = Box(
            style=Style(width=usable_w, height=body_h, flex_direction="row"),
            children=[hero_section, sidebar],
        )

        root = Box(
            style=Style(width=width, height=height, flex_direction="column",
                        padding=(inset_y, inset_x, inset_y, inset_x)),
            children=[accent_bar, body],
        )
        return render(root, width, height, background=_LIGHT_BG)
