"""Display driver wrapper that rotates the rendered image before showing it."""
from __future__ import annotations

from PIL import Image


class RotatedDisplayDriver:
    """Rotates each image counter-clockwise by ``degrees`` then delegates to ``inner``."""

    def __init__(self, inner, degrees: int) -> None:
        self._inner = inner
        self._degrees = degrees

    def show(self, image: Image.Image) -> None:
        self._inner.show(image.rotate(self._degrees, expand=True))

    def __getattr__(self, name):
        return getattr(self._inner, name)
