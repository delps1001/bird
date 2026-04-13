"""Filmstrip renderer: vertical filmstrip with sprocket holes and a countdown feel.

Visual concept: A vertical film strip — sprocket holes running down both
edges, each bird in its own "frame" stacked top to bottom. The #1 bird
gets a wider frame. Dark background evoking a cinema/darkroom vibe.
Works beautifully on portrait-oriented displays.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

_MIN_FONT = 6
_FILM_BG = (20, 20, 22)
_FRAME_BG = (35, 35, 38)
_SPROCKET = (55, 55, 58)
_WHITE = (235, 235, 230)
_MUTED = (140, 140, 135)
_AMBER = (240, 180, 60)



def _sprocket_strip(w: int, h: int, hole_count: int) -> Box:
    """Vertical strip of sprocket holes."""
    children: list[Box | Text | Img] = []
    hole_h = max(4, h // (hole_count * 3))
    gap_h = max(2, (h - hole_count * hole_h) // max(1, hole_count + 1))
    for _ in range(hole_count):
        children.append(Box(style=Style(width=w - 4, height=hole_h, background=_SPROCKET)))
    return Box(
        style=Style(
            width=w, height=h, flex_direction="column",
            justify_content="space_around", align_items="center",
            background=_FILM_BG,
        ),
        children=children,
    )


def _film_frame(
    bird: BirdSummary, assets_dir: Path,
    frame_w: int, frame_h: int, rank: int, is_hero: bool,
) -> Box:
    """One film frame: bird image with rank number and name below."""
    bird_img = load_bird_image(bird.common_name, assets_dir)
    pad = max(2, frame_w // 30)
    img_h = round(frame_h * (0.72 if is_hero else 0.65))
    text_h = frame_h - img_h

    name_sz = max(_MIN_FONT, text_h // 2)
    count_text = f"#{rank}  {bird.lifetime_count}x"
    count_sz = max(_MIN_FONT, text_h // 3)

    frame_border = (1, _MUTED) if not is_hero else (2, _AMBER)

    return Box(
        style=Style(
            width=frame_w, height=frame_h,
            border=frame_border, background=_FRAME_BG,
            flex_direction="column", align_items="center",
            padding=(pad, pad, pad, pad), overflow="hidden",
        ),
        children=[
            Img(src=bird_img, style=Style(
                width=frame_w - pad * 2, height=img_h - pad, object_fit="contain",
                image_rendering="pixelated",
            )),
            Text(bird.common_name, style=Style(
                font_size=name_sz,
                font_color=_AMBER if is_hero else _WHITE,
                text_align="center", padding=(2, 0, 0, 0),
                font_shrink=True,
            )),
            Text(count_text, style=Style(
                font_size=count_sz, font_color=_MUTED,
                text_align="center", font_shrink=True,
            )),
        ],
    )


class FilmstripRenderer:
    """Vertical cinema filmstrip layout — great for portrait displays."""

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
                style=Style(width=width, height=height, background=_FILM_BG,
                            padding=(inset_y, inset_x, inset_y, inset_x),
                            flex_direction="column", align_items="center", justify_content="center"),
                children=[
                    Text("[ NO EXPOSURES ]",
                         style=Style(font_size=max(_MIN_FONT, usable_h // 20), font_color=_MUTED)),
                ],
            )
            return render(tree, width, height, background=_FILM_BG)

        display = birds[:6]
        sprocket_w = max(12, usable_w // 18)
        frame_w = usable_w - sprocket_w * 2
        gap = max(2, usable_h // 80)

        # Hero gets more vertical space
        n = len(display)
        total_gap = gap * max(0, n - 1)
        hero_frac = 0.35 if n > 1 else 0.9
        hero_h = round((usable_h - total_gap) * hero_frac)
        remaining_h = usable_h - hero_h - total_gap
        other_h = max(20, remaining_h // max(1, n - 1)) if n > 1 else 0

        # Build frames
        frame_children: list[Box | Text | Img] = []
        for i, bird in enumerate(display):
            fh = hero_h if i == 0 else other_h
            frame_children.append(
                _film_frame(bird, assets_dir, frame_w, fh, rank=i + 1, is_hero=(i == 0))
            )

        # Sprocket holes
        hole_count = max(3, n * 2)
        left_sprockets = _sprocket_strip(sprocket_w, usable_h, hole_count)
        right_sprockets = _sprocket_strip(sprocket_w, usable_h, hole_count)

        # Center strip with frames
        center = Box(
            style=Style(
                width=frame_w, height=usable_h,
                flex_direction="column", align_items="center",
                justify_content="center", gap=gap,
                background=_FILM_BG,
            ),
            children=frame_children,
        )

        root = Box(
            style=Style(width=width, height=height, flex_direction="row", background=_FILM_BG,
                        padding=(inset_y, inset_x, inset_y, inset_x)),
            children=[left_sprockets, center, right_sprockets],
        )
        return render(root, width, height, background=_FILM_BG)
