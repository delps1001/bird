"""Waveshare 7.3inch e-Paper HAT (E) display driver.

6-color display (800x480): Black, White, Yellow, Red, Blue, Green.
The waveshare_epd library is only available on the Pi — the dither_to_palette()
function and palette constants can be used on any platform for preview/testing.
"""
from __future__ import annotations

from PIL import Image

WIDTH = 800
HEIGHT = 480

# The 6 colors supported by the 7.3e panel, in palette index order.
# Index 4 is unused (was orange on 7.3f) — mapped to black.
PALETTE_RGB: tuple[tuple[int, int, int], ...] = (
    (0, 0, 0),        # 0 — black
    (255, 255, 255),   # 1 — white
    (255, 255, 0),     # 2 — yellow
    (255, 0, 0),       # 3 — red
    (0, 0, 0),         # 4 — (unused, black)
    (0, 0, 255),       # 5 — blue
    (0, 255, 0),       # 6 — green
)


def _make_palette_image() -> Image.Image:
    """Build a 1x1 P-mode image carrying the panel's 7-slot palette."""
    pal = Image.new("P", (1, 1))
    flat = []
    for r, g, b in PALETTE_RGB:
        flat.extend((r, g, b))
    # Pad to 256 entries (required by PIL)
    flat.extend((0, 0, 0) * (256 - len(PALETTE_RGB)))
    pal.putpalette(flat)
    return pal


def dither_to_palette(image: Image.Image) -> Image.Image:
    """Quantize an RGB image to the 6-color e-ink palette with Floyd-Steinberg dithering.

    Returns a paletted (mode "P") Image. Works on any platform.
    """
    pal_image = _make_palette_image()
    return image.convert("RGB").quantize(palette=pal_image)


class EinkDisplayDriver:
    """Drives the Waveshare 7.3inch e-Paper HAT (E)."""

    def __init__(self) -> None:
        # Lazy import — waveshare_epd is only available on the Pi.
        # Install from the local e-Paper repo:
        #   pip install ./e-Paper/RaspberryPi_JetsonNano/python/lib/
        from waveshare_epd import epd7in3e as epd_module  # type: ignore[import-untyped]

        self._epd = epd_module.EPD()
        self._epd.init()

    def show(self, image: Image.Image) -> None:
        self._epd.display(self._epd.getbuffer(image))

    def clear(self) -> None:
        self._epd.Clear()

    def sleep(self) -> None:
        self._epd.sleep()
