"""Scoreboard renderer: sports-broadcast-style leaderboard with big rank numbers.

Visual concept: Think ESPN bottom-line ticker meets a retro arcade high-score
table. A bold header bar with the #1 bird's name scrolling. Below, a
leaderboard table with large rank numbers, bird thumbnails, species names,
and prominent lifetime/today counts in columns. Alternating row backgrounds.
A highlighted top row for the champion bird.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

_MIN_FONT = 6
_BG_DARK = (22, 27, 34)       # dark navy/charcoal
_BG_ROW_A = (30, 37, 46)
_BG_ROW_B = (38, 46, 56)
_GOLD = (255, 200, 50)
_SILVER = (190, 195, 205)
_BRONZE = (205, 150, 80)
_WHITE = (240, 240, 240)
_MUTED = (130, 140, 155)
_HEADER_BG = (255, 200, 50)
_HEADER_FG = (22, 27, 34)
_GREEN = (70, 200, 120)



_RANK_COLORS = {1: _GOLD, 2: _SILVER, 3: _BRONZE}


def _leaderboard_row(
    bird: BirdSummary, assets_dir: Path,
    row_w: int, row_h: int, rank: int, is_champ: bool,
) -> Box:
    """One leaderboard row: rank | thumbnail | name | lifetime | today."""
    bird_img = load_bird_image(bird.common_name, assets_dir)
    thumb_sz = max(14, row_h - 8)

    rank_w = max(28, row_w // 10)
    count_w = max(36, row_w // 8)
    name_w = row_w - rank_w - thumb_sz - count_w * 2 - 30  # gaps

    font_sz = max(_MIN_FONT, row_h // 3)
    name_sz = font_sz
    rank_color = _RANK_COLORS.get(rank, _MUTED)

    bg = _BG_DARK if is_champ else (_BG_ROW_A if rank % 2 == 0 else _BG_ROW_B)

    children = [
        # Rank
        Text(str(rank), style=Style(
            width=rank_w, font_size=max(_MIN_FONT, row_h // 2),
            font_color=rank_color, text_align="center", font_shrink=True,
        )),
        # Thumbnail
        Img(src=bird_img, style=Style(width=thumb_sz, height=thumb_sz, object_fit="contain", image_rendering="pixelated")),
        # Name
        Text(bird.common_name, style=Style(
            width=name_w, font_size=name_sz, font_color=_WHITE if is_champ else _SILVER,
            font_shrink=True,
        )),
        # Lifetime count
        Text(str(bird.lifetime_count), style=Style(
            width=count_w, font_size=font_sz, font_color=_WHITE, text_align="center",
            font_shrink=True,
        )),
        # Today count
        Text(str(bird.recent_count), style=Style(
            width=count_w, font_size=font_sz, font_color=_GREEN, text_align="center",
            font_shrink=True,
        )),
    ]

    if is_champ:
        # Add a gold left-border accent via a thin box
        children.insert(0, Box(style=Style(width=3, height=row_h, background=_GOLD)))

    return Box(
        style=Style(
            width=row_w, height=row_h, background=bg,
            flex_direction="row", align_items="center", gap=4,
            padding=(0, 4, 0, 4), overflow="hidden",
        ),
        children=children,
    )


def _column_header(row_w: int, row_h: int, rank_w: int, thumb_sz: int, name_w: int, count_w: int) -> Box:
    """Column labels row."""
    hdr_sz = max(_MIN_FONT, row_h * 2 // 3)
    return Box(
        style=Style(
            width=row_w, height=row_h, background=_BG_DARK,
            flex_direction="row", align_items="center", gap=4,
            padding=(0, 4, 0, 4),
        ),
        children=[
            Text("#", style=Style(width=rank_w, font_size=hdr_sz, font_color=_MUTED, text_align="center", font_shrink=True)),
            Box(style=Style(width=thumb_sz, height=1)),  # spacer for thumbnail
            Text("SPECIES", style=Style(width=name_w, font_size=hdr_sz, font_color=_MUTED, font_shrink=True)),
            Text("ALL", style=Style(width=count_w, font_size=hdr_sz, font_color=_MUTED, text_align="center", font_shrink=True)),
            Text("TODAY", style=Style(width=count_w, font_size=hdr_sz, font_color=_MUTED, text_align="center", font_shrink=True)),
        ],
    )


class ScoreboardRenderer:
    """ESPN-style bird leaderboard."""

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
        usable_w = width - 2 * inset_x
        usable_h = height - 2 * inset_y

        if not birds:
            tree = Box(
                style=Style(width=width, height=height, background=_BG_DARK,
                            padding=(inset_y, inset_x, inset_y, inset_x),
                            flex_direction="column", align_items="center", justify_content="center"),
                children=[
                    Text("AWAITING FIRST DETECTION...",
                         style=Style(font_size=max(_MIN_FONT, usable_h // 16), font_color=_MUTED)),
                ],
            )
            return render(tree, width, height, background=_BG_DARK)

        display = birds[:6]
        hero = display[0]

        # Header bar
        header_h = max(20, usable_h // 10)
        ticker_text = f"  #{1} {hero.common_name.upper()} - {hero.lifetime_count}x LIFETIME DETECTIONS"
        ticker_sz = max(10, header_h - 8)
        header = Box(
            style=Style(
                width=usable_w, height=header_h, background=_HEADER_BG,
                flex_direction="row", align_items="center", padding=(0, 10, 0, 10),
            ),
            children=[
                Text(ticker_text, style=Style(font_size=ticker_sz, font_color=_HEADER_FG, font_shrink=True)),
            ],
        )

        # Sub-header with latest detection
        sub_h = max(12, usable_h // 24)
        latest = None
        for b in display:
            if b.last_detected_at and (latest is None or b.last_detected_at > latest.last_detected_at):
                latest = b
        if latest and latest.last_detected_at:
            time_str = latest.last_detected_at.strftime("%-I:%M %p")
            sub_text = f"Latest: {latest.common_name} @ {time_str}"
        else:
            sub_text = f"{len(display)} species ranked"
        sub_sz = max(_MIN_FONT, sub_h - 4)
        subheader = Box(
            style=Style(
                width=usable_w, height=sub_h, background=(35, 42, 52),
                flex_direction="row", align_items="center", padding=(0, 10, 0, 10),
            ),
            children=[Text(sub_text, style=Style(font_size=sub_sz, font_color=_GREEN, font_shrink=True))],
        )

        # Table area
        table_h = usable_h - header_h - sub_h
        row_w = usable_w
        col_hdr_h = max(12, table_h // 18)

        # Compute column widths (same as row internals)
        thumb_sz = max(14, (table_h - col_hdr_h) // max(1, len(display)) - 8)
        thumb_sz = min(thumb_sz, 48)
        rank_w = max(28, row_w // 10)
        count_w = max(36, row_w // 8)
        name_w = row_w - rank_w - thumb_sz - count_w * 2 - 30

        table_children: list[Box | Text | Img] = []
        table_children.append(_column_header(row_w, col_hdr_h, rank_w, thumb_sz, name_w, count_w))

        # Divider
        table_children.append(Box(style=Style(width=row_w, height=1, background=_MUTED)))

        row_h = max(20, (table_h - col_hdr_h - 1) // max(1, len(display)))
        for i, bird in enumerate(display):
            table_children.append(
                _leaderboard_row(bird, assets_dir, row_w, row_h, rank=i + 1, is_champ=(i == 0))
            )

        table = Box(
            style=Style(width=usable_w, height=table_h, flex_direction="column", background=_BG_DARK),
            children=table_children,
        )

        root = Box(
            style=Style(width=width, height=height, flex_direction="column",
                        padding=(inset_y, inset_x, inset_y, inset_x)),
            children=[header, subheader, table],
        )
        return render(root, width, height, background=_BG_DARK)
