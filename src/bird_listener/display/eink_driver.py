"""Waveshare e-ink display driver for Raspberry Pi.

This module is only used on the Pi — import will fail on macOS
since the waveshare_epd library depends on RPi.GPIO.
"""
from __future__ import annotations

from PIL import Image


class EinkDisplayDriver:
    """Drives a Waveshare e-ink display."""

    def __init__(self, model: str = "epd7in5_V2") -> None:
        # Lazy import so this module can be loaded for type checking
        # without the waveshare library installed
        from waveshare_epd import epd7in5_V2 as epd_module  # type: ignore[import-untyped]

        self._epd = epd_module.EPD()
        self._epd.init()

    def show(self, image: Image.Image) -> None:
        self._epd.display(self._epd.getbuffer(image))

    def sleep(self) -> None:
        self._epd.sleep()
