from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import ImageFont


_font_cache: dict[tuple[Optional[str], int], ImageFont.FreeTypeFont] = {}

_BUNDLED_FONT = str(Path(__file__).parent / "DejaVuSans.ttf")


def load_font(path: Optional[str] = None, size: int = 16) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key in _font_cache:
        return _font_cache[key]

    try:
        if path:
            font = ImageFont.truetype(path, size)
        else:
            font = ImageFont.truetype(_BUNDLED_FONT, size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except (OSError, IOError):
            font = ImageFont.load_default(size=size)

    _font_cache[key] = font
    return font
