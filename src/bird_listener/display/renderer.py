from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from bird_listener.display.layout import (
    DEFAULT_LAYOUT,
    DisplayLayout,
    fit_image,
    resolve,
    scale_font_size,
)
from bird_listener.persistence.models import BirdSummary


def _species_to_filename(common_name: str) -> str:
    """Convert 'House Finch' to 'house_finch.png'."""
    return common_name.lower().replace(" ", "_").replace("-", "_") + ".png"


def _load_bird_image(common_name: str, assets_dir: Path) -> Image.Image:
    """Load species pixel art, falling back to _default.png."""
    species_path = assets_dir / _species_to_filename(common_name)
    if species_path.exists():
        return Image.open(species_path).convert("RGBA")
    default_path = assets_dir / "_default.png"
    if default_path.exists():
        return Image.open(default_path).convert("RGBA")
    # Last resort: generate a placeholder square
    img = Image.new("RGBA", (32, 32), (180, 180, 180, 255))
    return img


def _try_load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a clean font, fall back to default."""
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial Bold.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


class PillowRenderer:
    def __init__(self, layout: DisplayLayout | None = None) -> None:
        self._layout = layout or DEFAULT_LAYOUT

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        pad = round(self._layout.padding * min(width, height))

        if not birds:
            font = _try_load_font(scale_font_size(20, height))
            draw.text((pad, pad), "No birds detected yet", fill=(100, 100, 100), font=font)
            return canvas

        # Hero region: rarest bird
        self._draw_hero(canvas, draw, birds[0], assets_dir, width, height, pad)

        # Secondary region: 2nd and 3rd rarest
        if len(birds) >= 2:
            secondary_birds = birds[1: 1 + self._layout.secondary_columns]
            self._draw_secondary(canvas, draw, secondary_birds, assets_dir, width, height, pad)

        return canvas

    def _draw_hero(
        self,
        canvas: Image.Image,
        draw: ImageDraw.Draw,
        bird: BirdSummary,
        assets_dir: Path,
        width: int,
        height: int,
        pad: int,
    ) -> None:
        layout = self._layout
        hx, hy, hw, hh = resolve(layout.hero, width, height)
        hx += pad
        hy += pad
        hw -= 2 * pad
        hh -= pad  # only top padding for hero

        img_h = round(hh * layout.hero_image_area)
        text_h = hh - img_h

        # Draw bird image centered in hero image area
        bird_img = _load_bird_image(bird.common_name, assets_dir)
        bird_img = fit_image(bird_img, hw, img_h)
        img_x = hx + (hw - bird_img.width) // 2
        img_y = hy + (img_h - bird_img.height) // 2
        canvas.paste(bird_img, (img_x, img_y), bird_img if bird_img.mode == "RGBA" else None)

        # Draw bird name
        name_size = scale_font_size(28, height)
        name_font = _try_load_font(name_size)
        name_y = hy + img_h + (text_h // 6)
        bbox = draw.textbbox((0, 0), bird.common_name, font=name_font)
        text_w = bbox[2] - bbox[0]
        name_x = hx + (hw - text_w) // 2
        draw.text((name_x, name_y), bird.common_name, fill=(0, 0, 0), font=name_font)

        # Draw count info
        info = f"Seen {bird.lifetime_count}x lifetime, {bird.recent_count}x today"
        info_size = scale_font_size(14, height)
        info_font = _try_load_font(info_size)
        info_bbox = draw.textbbox((0, 0), info, font=info_font)
        info_w = info_bbox[2] - info_bbox[0]
        info_y = name_y + name_size + 4
        draw.text(
            (hx + (hw - info_w) // 2, info_y),
            info,
            fill=(80, 80, 80),
            font=info_font,
        )

    def _draw_secondary(
        self,
        canvas: Image.Image,
        draw: ImageDraw.Draw,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
        pad: int,
    ) -> None:
        layout = self._layout
        sx, sy, sw, sh = resolve(layout.secondary, width, height)
        sx += pad
        sy += pad // 2
        sw -= 2 * pad
        sh -= pad

        col_w = sw // layout.secondary_columns

        for i, bird in enumerate(birds):
            cx = sx + i * col_w
            img_area_h = round(sh * 0.60)
            text_area_h = sh - img_area_h

            # Bird image
            bird_img = _load_bird_image(bird.common_name, assets_dir)
            bird_img = fit_image(bird_img, col_w - pad, img_area_h)
            img_x = cx + (col_w - bird_img.width) // 2
            img_y = sy + (img_area_h - bird_img.height) // 2
            canvas.paste(bird_img, (img_x, img_y), bird_img if bird_img.mode == "RGBA" else None)

            # Bird name
            name_size = scale_font_size(16, height)
            name_font = _try_load_font(name_size)
            name_y = sy + img_area_h
            bbox = draw.textbbox((0, 0), bird.common_name, font=name_font)
            tw = bbox[2] - bbox[0]
            draw.text(
                (cx + (col_w - tw) // 2, name_y),
                bird.common_name,
                fill=(0, 0, 0),
                font=name_font,
            )

            # Count
            count_text = f"{bird.lifetime_count}x"
            count_size = scale_font_size(12, height)
            count_font = _try_load_font(count_size)
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            cw = count_bbox[2] - count_bbox[0]
            draw.text(
                (cx + (col_w - cw) // 2, name_y + name_size + 2),
                count_text,
                fill=(80, 80, 80),
                font=count_font,
            )
