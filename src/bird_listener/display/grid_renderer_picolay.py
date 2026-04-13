"""Grid renderer reimplemented using the picolay layout engine.

Drop-in replacement for GridRenderer — same public interface, same visual
output, but all layout is declarative via picolay instead of manual pixel math.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.display.grid_layout import DEFAULT_GRID_LAYOUT, GridDisplayLayout
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

# Proportions matching grid_layout.py
_SIDE_W_FRAC = 0.22
_CENTER_W_FRAC = 1.0 - 2 * _SIDE_W_FRAC
_TOP_H_FRAC = 0.65
_BOT_H_FRAC = 1.0 - _TOP_H_FRAC

# Card style constants (matching bird_card.py CardStyle values)
_HERO_IMAGE_FRAC = 0.70
_HERO_NAME_FONT_FRAC = 0.35
_HERO_INFO_FONT_FRAC = 0.18
_SEC_IMAGE_FRAC = 0.60
_SEC_NAME_FONT_FRAC = 0.30
_SEC_INFO_FONT_FRAC = 0.16

_TEXT_COLOR = (0, 0, 0)
_INFO_COLOR = (80, 80, 80)
_FOOTER_FONT_FRAC = 0.50
_MIN_FONT = 6


def _bird_card_tree(
    bird: BirdSummary,
    assets_dir: Path,
    cell_w: int,
    cell_h: int,
    is_hero: bool,
    info_format: str = "{lifetime_count}x lifetime, {recent_count}x today",
) -> Box:
    """Build a picolay node tree for a single bird card."""
    image_frac = _HERO_IMAGE_FRAC if is_hero else _SEC_IMAGE_FRAC
    name_font_frac = _HERO_NAME_FONT_FRAC if is_hero else _SEC_NAME_FONT_FRAC
    info_font_frac = _HERO_INFO_FONT_FRAC if is_hero else _SEC_INFO_FONT_FRAC

    img_h = round(cell_h * image_frac)
    text_h = cell_h - img_h

    # Load bird image
    bird_img = load_bird_image(bird.common_name, assets_dir)

    name_size = max(_MIN_FONT, round(text_h * name_font_frac))

    format_fields = {
        "common_name": bird.common_name,
        "scientific_name": bird.scientific_name,
        "lifetime_count": bird.lifetime_count,
        "recent_count": bird.recent_count,
        "best_confidence": bird.best_confidence,
    }
    info_text = info_format.format_map(format_fields)
    info_size = max(_MIN_FONT, round(text_h * info_font_frac))

    return Box(
        style=Style(
            width=cell_w,
            height=cell_h,
            flex_direction="column",
            align_items="center",
            overflow="hidden",
        ),
        children=[
            # Image region
            Img(
                src=bird_img,
                style=Style(width=cell_w, height=img_h, object_fit="contain", image_rendering="pixelated"),
            ),
            # Species name
            Text(
                bird.common_name,
                style=Style(
                    width=cell_w,
                    font_size=name_size,
                    font_color=_TEXT_COLOR,
                    text_align="center",
                    padding=(max(1, text_h // 6), 0, 0, 0),
                    font_shrink=True,
                ),
            ),
            # Info line
            Text(
                info_text,
                style=Style(
                    width=cell_w,
                    font_size=info_size,
                    font_color=_INFO_COLOR,
                    text_align="center",
                    padding=(4, 0, 0, 0),
                    font_shrink=True,
                ),
            ),
        ],
    )


def _footer_tree(
    birds: list[BirdSummary],
    assets_dir: Path,
    fw: int,
    fh: int,
) -> Box | None:
    """Build the 'last detected' footer bar, or None if no timestamps."""
    latest_bird = None
    for bird in birds:
        if bird.last_detected_at is not None:
            if latest_bird is None or bird.last_detected_at > latest_bird.last_detected_at:
                latest_bird = bird

    if latest_bird is None:
        return None

    time_str = latest_bird.last_detected_at.strftime("%-I:%M %p")
    text = f"{latest_bird.common_name} @ {time_str}"

    font_size = max(_MIN_FONT, round(fh * _FOOTER_FONT_FRAC))
    bird_img = load_bird_image(latest_bird.common_name, assets_dir)
    gap = max(2, font_size // 4)

    return Box(
        style=Style(
            width=fw,
            height=fh,
            flex_direction="row",
            align_items="center",
            justify_content="center",
            gap=gap,
        ),
        children=[
            Img(
                src=bird_img,
                style=Style(width=font_size * 2, height=font_size, object_fit="contain", image_rendering="pixelated"),
            ),
            Text(
                text,
                style=Style(font_size=font_size, font_color=(100, 100, 100), font_shrink=True),
            ),
        ],
    )


class PicolayGridRenderer:
    """Renders up to 6 birds in a grid with a 'last detected' footer.

    Same visual output as GridRenderer, built with picolay.
    """

    def __init__(self, layout: GridDisplayLayout | None = None) -> None:
        self._layout = layout or DEFAULT_GRID_LAYOUT

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        lay = self._layout
        inset_x = round(lay.inset * width)
        inset_y = round(lay.inset * height)
        usable_w = width - 2 * inset_x
        usable_h = height - 2 * inset_y

        grid_h = round(usable_h * lay.grid_height_frac)
        footer_h = round(usable_h * lay.footer_height_frac)

        if not birds:
            fh = footer_h if footer_h > 0 else round(usable_h * 0.05)
            font_size = max(_MIN_FONT, round(fh * _FOOTER_FONT_FRAC))
            tree = Box(
                style=Style(width=width, height=height, padding=(inset_y, inset_x, inset_y, inset_x)),
                children=[
                    Text(
                        "No birds detected yet",
                        style=Style(font_size=font_size, font_color=(100, 100, 100), padding=(10, 0, 0, 10)),
                    ),
                ],
            )
            return render(tree, width, height)

        display_birds = birds[:6]

        # Compute grid cell pixel sizes using the same proportions as GridDisplayLayout
        top_h = round(grid_h * _TOP_H_FRAC)
        bot_h = grid_h - top_h
        side_w = round(usable_w * _SIDE_W_FRAC)
        center_w = usable_w - 2 * side_w

        side_h = bot_h
        side_y_offset = (top_h - side_h) // 2

        # Build card trees for each bird (up to 6)
        def card(i: int, cw: int, ch: int) -> Box:
            return _bird_card_tree(display_birds[i], assets_dir, cw, ch, is_hero=(i == 0))

        num = len(display_birds)

        # Top section: side-left | hero | side-right
        top_children = []

        # Left side column (rank 1 = 2nd bird)
        if num > 1:
            left_card = card(1, side_w, side_h)
        else:
            left_card = Box(style=Style(width=side_w, height=side_h))
        left_col = Box(
            style=Style(
                width=side_w,
                height=top_h,
                flex_direction="column",
                justify_content="center",
                align_items="center",
            ),
            children=[left_card],
        )
        top_children.append(left_col)

        # Hero (rank 0)
        hero_card = card(0, center_w, top_h)
        top_children.append(hero_card)

        # Right side column (rank 5 = 6th bird)
        if num > 5:
            right_card = card(5, side_w, side_h)
        else:
            right_card = Box(style=Style(width=side_w, height=side_h))
        right_col = Box(
            style=Style(
                width=side_w,
                height=top_h,
                flex_direction="column",
                justify_content="center",
                align_items="center",
            ),
            children=[right_card],
        )
        top_children.append(right_col)

        top_row = Box(
            style=Style(width=usable_w, height=top_h, flex_direction="row"),
            children=top_children,
        )

        # Bottom section: 3 columns (rank 2, 3, 4)
        bot_children = []
        for rank_i in (2, 3, 4):
            if rank_i < num:
                bot_children.append(card(rank_i, side_w if rank_i != 3 else center_w, bot_h))
            else:
                col_w = side_w if rank_i != 3 else center_w
                bot_children.append(Box(style=Style(width=col_w, height=bot_h)))

        bot_row = Box(
            style=Style(width=usable_w, height=bot_h, flex_direction="row"),
            children=bot_children,
        )

        # Grid
        grid_children: list[Box | Text | Img] = [top_row, bot_row]

        # Footer
        footer_node = None
        if footer_h > 0 and display_birds:
            footer_node = _footer_tree(display_birds, assets_dir, usable_w, footer_h)
            if footer_node is not None:
                grid_children.append(footer_node)

        grid = Box(
            style=Style(width=usable_w, flex_direction="column"),
            children=grid_children,
        )

        # Root with inset padding
        root = Box(
            style=Style(width=width, height=height, padding=(inset_y, inset_x, inset_y, inset_x)),
            children=[grid],
        )

        return render(root, width, height)
