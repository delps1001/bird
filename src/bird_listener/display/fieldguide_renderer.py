"""Field guide renderer: elegant naturalist's journal, two-column botanical style.

Visual concept: A vintage field notebook page. Warm parchment background.
The hero bird is drawn large on the left with a hand-written-style label.
The right column shows a ranked list with small thumbnails, scientific names
in italics (simulated via smaller font), and detection counts. A decorative
horizontal rule separates the hero from the catalog. A subtle page border
(thin inset line) frames everything.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

_MIN_FONT = 6
_INK = (55, 40, 30)
_INK_LIGHT = (120, 100, 80)
_RULE_COLOR = (190, 175, 155)
_ACCENT = (140, 60, 40)       # sepia red for rank highlights



def _catalog_entry(bird: BirdSummary, assets_dir: Path, w: int, h: int, rank: int) -> Box:
    """One catalog entry: number dot, thumbnail, common + scientific name, count."""
    bird_img = load_bird_image(bird.common_name, assets_dir)
    thumb = min(max(14, h - 6), 48)
    text_w = w - thumb - 30

    name_sz = max(_MIN_FONT, h // 3)
    count_text = "\u2605" if bird.is_new else f"{bird.lifetime_count}x"

    return Box(
        style=Style(
            width=w, height=h,
            flex_direction="row", align_items="center",
            gap=4, padding=(0, 4, 0, 0), overflow="hidden",
        ),
        children=[
            Text(f"{rank}.", style=Style(
                width=18, font_size=max(_MIN_FONT, h // 3), font_color=_ACCENT, text_align="right",
                font_shrink=True,
            )),
            Img(src=bird_img, style=Style(width=thumb, height=thumb, object_fit="contain", image_rendering="pixelated")),
            Box(
                style=Style(flex_grow=1, flex_direction="column", justify_content="center"),
                children=[
                    Text(bird.common_name, style=Style(font_size=name_sz, font_color=_INK, font_shrink=True)),
                ],
            ),
            Text(count_text, style=Style(
                font_size=max(_MIN_FONT, h // 3), font_color=_ACCENT, text_align="right",
                padding=(0, 4, 0, 0), font_shrink=True,
            )),
        ],
    )


def _h_rule(w: int) -> Box:
    return Box(style=Style(width=w, height=1, background=_RULE_COLOR))


class FieldGuideRenderer:
    """Vintage naturalist field-guide layout."""

    def __init__(self, inset: float = 0.0, max_birds: int = 5):
        self._inset = inset
        self._max_birds = max_birds

    @property
    def max_birds(self) -> int:
        return self._max_birds

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

        inner_w = usable_w
        inner_h = usable_h

        if not birds:
            tree = Box(
                style=Style(width=width, height=height,
                            padding=(inset_y, inset_x, inset_y, inset_x),
                            flex_direction="column", align_items="center", justify_content="center"),
                children=[
                    Text("~ No specimens recorded ~",
                         style=Style(font_size=max(_MIN_FONT, usable_h // 18), font_color=_INK_LIGHT)),
                ],
            )
            return render(tree, width, height, background=(255, 255, 255))

        display = birds[:self._max_birds]
        hero = display[0]

        # Two-column split
        left_w = round(inner_w * 0.45)
        right_w = inner_w - left_w

        # --- Left: hero bird study ---
        hero_img = load_bird_image(hero.common_name, assets_dir)
        title_sz = max(10, inner_h // 10)
        sci_sz = max(_MIN_FONT, title_sz * 2 // 3)
        img_h = round(inner_h * 0.50)
        label_h = inner_h - img_h - 16 - 1

        s = "s"
        if hero.lifetime_count == 1:
            s = ""

        hero_count_text = "\u2605" if hero.is_new else f"{hero.lifetime_count}x"

        left_col = Box(
            style=Style(
                width=left_w, height=inner_h,
                flex_direction="column", align_items="center",
                padding=(8, 8, 8, 8),
            ),
            children=[
                Img(src=hero_img, style=Style(width=left_w - 16, height=img_h, object_fit="contain", image_rendering="pixelated")),
                _h_rule(left_w - 32),
                Box(
                    style=Style(
                        width=left_w - 16, height=label_h, flex_direction="column",
                        align_items="center", justify_content="center",
                        padding=(6, 0, 0, 0),
                    ),
                    children=[
                        Text(hero.common_name, style=Style(
                            font_size=title_sz, font_color=_INK, text_align="center",
                            font_shrink=True,
                        )),
                        Text(hero.scientific_name, style=Style(
                            font_size=sci_sz, font_color=_INK_LIGHT, text_align="center",
                            font_shrink=True,
                        )),
                        Text(
                            hero_count_text,
                            style=Style(
                                font_size=max(_MIN_FONT, sci_sz - 2), font_color=_INK_LIGHT,
                                text_align="center", padding=(4, 0, 0, 0),
                                font_shrink=True,
                            ),
                        ),
                    ],
                ),
            ],
        )


        # Vertical divider
        v_div = Box(style=Style(width=1, height=inner_h, background=_RULE_COLOR))

        # --- Right: catalog of remaining species ---
        catalog_children: list[Box | Text | Img] = []
        cat_header_sz = max(_MIN_FONT, inner_h // 18)
        cat_header_h = cat_header_sz + 16  # font + padding
        catalog_children.append(Box(
            style=Style(
                width=right_w, height=cat_header_h,
                flex_direction="column", align_items="center",
                justify_content="center",
            ),
            children=[
                Text("Recent Sightings", style=Style(
                    font_size=cat_header_sz, font_color=_ACCENT, text_align="center",
                    font_shrink=True,
                )),
            ],
        ))
        catalog_children.append(_h_rule(right_w - 16))

        others = display[1:]
        if others:
            available_cat_h = inner_h - cat_header_h - 1
            n = len(others)
            row_h = (available_cat_h - max(0, n - 1)) // n
            for i, bird in enumerate(others):
                catalog_children.append(
                    _catalog_entry(bird, assets_dir, right_w - 8, row_h, rank=i + 2)
                )
                if i < len(others) - 1:
                    catalog_children.append(_h_rule(right_w - 24))
        else:
            catalog_children.append(
                Text("No other species", style=Style(
                    font_size=max(_MIN_FONT, inner_h // 20), font_color=_INK_LIGHT,
                    padding=(20, 0, 0, 0),
                ))
            )

        right_col = Box(
            style=Style(width=right_w, height=inner_h, flex_direction="column"),
            children=catalog_children,
        )

        body = Box(
            style=Style(width=inner_w, height=inner_h, flex_direction="row"),
            children=[left_col, v_div, right_col],
        )

        # Thin page border via nested boxes
        root = Box(
            style=Style(
                width=width, height=height,
                padding=(inset_y, inset_x, inset_y, inset_x),
                flex_direction="column", align_items="center", justify_content="center",
            ),
            children=[
                Box(
                    style=Style(
                        width=inner_w, height=inner_h,
                        flex_direction="column", align_items="center", justify_content="center",
                    ),
                    children=[body],
                ),
            ],
        )
        return render(root, width, height, background=(255, 255, 255))
