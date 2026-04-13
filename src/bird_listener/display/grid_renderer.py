"""Grid renderer for e-ink display with hero-prominent layout."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from bird_listener.display.bird_card import (
    HERO_STYLE,
    SECONDARY_STYLE,
    draw_bird_card,
)
from bird_listener.display.common import load_bird_image, try_load_font
from bird_listener.display.grid_layout import DEFAULT_GRID_LAYOUT, GridDisplayLayout
from bird_listener.display.layout import fit_image, resolve
from bird_listener.persistence.models import BirdSummary

# Footer font as fraction of footer region height
_FOOTER_FONT_FRAC = 0.50
_MIN_FONT = 6


class GridRenderer:
    """Renders up to 6 birds in a grid with a 'last detected' footer."""

    def __init__(self, layout: GridDisplayLayout | None = None) -> None:
        self._layout = layout or DEFAULT_GRID_LAYOUT

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        if not birds:
            footer = self._layout.footer_region()
            _, _, _, fh = resolve(footer, width, height)
            font_size = max(_MIN_FONT, round(fh * _FOOTER_FONT_FRAC))
            font = try_load_font(font_size)
            inset_x = round(self._layout.inset * width)
            inset_y = round(self._layout.inset * height)
            draw.text((inset_x + 10, inset_y + 10), "No birds detected yet", fill=(100, 100, 100), font=font)
            return canvas

        cell_regions = self._layout.cell_regions()
        display_birds = birds[:6]

        for i, bird in enumerate(display_birds):
            region = cell_regions[i]
            x, y, w, h = resolve(region, width, height)
            style = HERO_STYLE if i == 0 else SECONDARY_STYLE
            draw_bird_card(canvas, draw, bird, assets_dir, x, y, w, h, style)

        # Footer: show most recently detected bird (if enabled)
        if self._layout.footer_height_frac > 0:
            self._draw_footer(canvas, draw, display_birds, assets_dir, width, height)

        return canvas

    def _draw_footer(
        self,
        canvas: Image.Image,
        draw: ImageDraw.Draw,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> None:
        # Find the bird with the latest detection time
        latest_bird = None
        for bird in birds:
            if bird.last_detected_at is not None:
                if latest_bird is None or bird.last_detected_at > latest_bird.last_detected_at:
                    latest_bird = bird

        if latest_bird is None:
            return

        footer = self._layout.footer_region()
        fx, fy, fw, fh = resolve(footer, width, height)

        time_str = latest_bird.last_detected_at.strftime("%-I:%M %p")
        # Clock symbol + species name + time
        text = f"{latest_bird.common_name} @ {time_str}"

        font_size = max(_MIN_FONT, round(fh * _FOOTER_FONT_FRAC))
        font = try_load_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Load a tiny bird preview at the same pixel height as the text
        bird_img = load_bird_image(latest_bird.common_name, assets_dir)
        bird_img = fit_image(bird_img, font_size * 2, font_size)

        # Total content width: bird preview + gap + text
        gap = max(2, font_size // 4)
        total_w = bird_img.width + gap + text_w
        start_x = fx + (fw - total_w) // 2
        cy = fy + (fh - font_size) // 2

        # Paste bird preview
        canvas.paste(
            bird_img,
            (start_x, cy),
            bird_img if bird_img.mode == "RGBA" else None,
        )

        # Draw text after the preview
        tx = start_x + bird_img.width + gap
        ty = fy + (fh - text_h) // 2
        draw.text((tx, ty), text, fill=(100, 100, 100), font=font)
