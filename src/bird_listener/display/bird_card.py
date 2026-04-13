"""Reusable bird card component for rendering a single bird into a rect."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bird_listener.display.common import load_bird_image, try_load_font
from bird_listener.display.layout import fit_image
from bird_listener.persistence.models import BirdSummary

# Minimum font size in pixels — below this text is unreadable.
_MIN_FONT = 6


@dataclass(frozen=True)
class CardStyle:
    """Visual style parameters for a bird card.

    Font sizes are expressed as fractions of the card's *text area* height
    (the portion below the image). This makes cards scale naturally to any
    cell size, display resolution, or inset value.
    """

    image_area_frac: float  # fraction of card height for the image
    name_font_frac: float  # name font size as fraction of text area height
    info_font_frac: float  # info font size as fraction of text area height
    text_color: tuple[int, int, int]
    info_color: tuple[int, int, int]


HERO_STYLE = CardStyle(
    image_area_frac=0.70,
    name_font_frac=0.35,
    info_font_frac=0.18,
    text_color=(0, 0, 0),
    info_color=(80, 80, 80),
)

SECONDARY_STYLE = CardStyle(
    image_area_frac=0.60,
    name_font_frac=0.30,
    info_font_frac=0.16,
    text_color=(0, 0, 0),
    info_color=(80, 80, 80),
)


def _fit_font(
    draw: ImageDraw.Draw,
    text: str,
    target_size: int,
    max_width: int,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, int]:
    """Return a font sized so *text* fits within *max_width* pixels.

    Starts at *target_size* and shrinks until the text fits or _MIN_FONT is
    reached.  Returns (font, actual_size).
    """
    size = target_size
    while size > _MIN_FONT:
        font = try_load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font, size
        size -= 1
    font = try_load_font(_MIN_FONT)
    return font, _MIN_FONT


def draw_bird_card(
    canvas: Image.Image,
    draw: ImageDraw.Draw,
    bird: BirdSummary,
    assets_dir: Path,
    x: int,
    y: int,
    w: int,
    h: int,
    style: CardStyle,
    info_format: str = "{lifetime_count}x lifetime, {recent_count}x today",
) -> None:
    """Render one bird (image + name + stat line) into the given rect.

    All sizing (image, fonts) is derived from the card dimensions *w* and *h*,
    so the card scales correctly at any resolution or inset.  Text is
    guaranteed to fit within the card width.
    """
    if w <= 0 or h <= 0:
        return

    img_h = round(h * style.image_area_frac)
    text_h = h - img_h

    # Draw bird image centered in image area
    bird_img = load_bird_image(bird.common_name, assets_dir)
    bird_img = fit_image(bird_img, w, img_h)
    img_x = x + (w - bird_img.width) // 2
    img_y = y + (img_h - bird_img.height) // 2
    canvas.paste(bird_img, (img_x, img_y), bird_img if bird_img.mode == "RGBA" else None)

    # Derive initial font sizes from the card's text area
    name_target = max(_MIN_FONT, round(text_h * style.name_font_frac))
    info_target = max(_MIN_FONT, round(text_h * style.info_font_frac))

    # Fit name font to card width
    name_font, name_size = _fit_font(draw, bird.common_name, name_target, w)

    # Draw species name centered below image
    name_y = y + img_h + (text_h // 6)
    bbox = draw.textbbox((0, 0), bird.common_name, font=name_font)
    text_w = bbox[2] - bbox[0]
    name_x = x + (w - text_w) // 2
    draw.text((name_x, name_y), bird.common_name, fill=style.text_color, font=name_font)

    # Build info text
    format_fields = {
        "common_name": bird.common_name,
        "scientific_name": bird.scientific_name,
        "lifetime_count": bird.lifetime_count,
        "recent_count": bird.recent_count,
        "best_confidence": bird.best_confidence,
    }
    info_text = info_format.format_map(format_fields)

    # Fit info font to card width
    info_font, info_size = _fit_font(draw, info_text, info_target, w)

    info_bbox = draw.textbbox((0, 0), info_text, font=info_font)
    info_w = info_bbox[2] - info_bbox[0]
    info_y = name_y + name_size + 4
    draw.text(
        (x + (w - info_w) // 2, info_y),
        info_text,
        fill=style.info_color,
        font=info_font,
    )
