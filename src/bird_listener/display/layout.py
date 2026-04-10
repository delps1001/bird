from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class LayoutRegion:
    """A region defined as fractions (0.0–1.0) of the canvas."""
    x_frac: float
    y_frac: float
    w_frac: float
    h_frac: float


@dataclass(frozen=True)
class DisplayLayout:
    padding: float  # fraction of canvas for border padding
    hero: LayoutRegion  # top region for rarest bird
    hero_image_area: float  # fraction of hero height for the image (rest is text)
    secondary: LayoutRegion  # bottom region for runner-up birds
    secondary_columns: int  # number of columns in secondary region


DEFAULT_LAYOUT = DisplayLayout(
    padding=0.03,
    hero=LayoutRegion(x_frac=0.0, y_frac=0.0, w_frac=1.0, h_frac=0.65),
    hero_image_area=0.70,
    secondary=LayoutRegion(x_frac=0.0, y_frac=0.65, w_frac=1.0, h_frac=0.35),
    secondary_columns=2,
)


def resolve(region: LayoutRegion, canvas_w: int, canvas_h: int) -> tuple[int, int, int, int]:
    """Convert fractional region to pixel coordinates (x, y, w, h)."""
    x = round(region.x_frac * canvas_w)
    y = round(region.y_frac * canvas_h)
    w = round(region.w_frac * canvas_w)
    h = round(region.h_frac * canvas_h)
    return x, y, w, h


def fit_image(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Scale image to fit within max_w x max_h, preserving aspect ratio.

    Uses NEAREST interpolation to keep pixel art crisp.
    """
    if max_w <= 0 or max_h <= 0:
        return image

    orig_w, orig_h = image.size
    if orig_w <= 0 or orig_h <= 0:
        return image

    scale = min(max_w / orig_w, max_h / orig_h)
    new_w = max(1, round(orig_w * scale))
    new_h = max(1, round(orig_h * scale))
    return image.resize((new_w, new_h), Image.NEAREST)


def scale_font_size(base_size: int, canvas_height: int, reference_height: int = 480) -> int:
    """Scale font size proportionally to canvas height."""
    if reference_height <= 0:
        return base_size
    return max(1, round(base_size * canvas_height / reference_height))
