"""Shared display utilities for bird renderers."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFont


def species_to_filename(common_name: str) -> str:
    """Convert 'House Finch' to 'house_finch.png'."""
    return common_name.lower().replace(" ", "_").replace("-", "_") + ".png"


def load_bird_image(common_name: str, assets_dir: Path) -> Image.Image:
    """Load species pixel art, falling back to _default.png."""
    species_path = assets_dir / species_to_filename(common_name)
    if species_path.exists():
        return Image.open(species_path).convert("RGBA")
    default_path = assets_dir / "_default.png"
    if default_path.exists():
        return Image.open(default_path).convert("RGBA")
    # Last resort: generate a placeholder square
    return Image.new("RGBA", (32, 32), (180, 180, 180, 255))


def try_load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a clean font, fall back to default."""
    for name in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "Arial Bold.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()
