"""Tests for the e-ink dithering / palette quantization."""
from __future__ import annotations

from PIL import Image

from bird_listener.display.eink_driver import PALETTE_RGB, dither_to_palette


def _solid(color: tuple[int, int, int], size: tuple[int, int] = (80, 48)) -> Image.Image:
    return Image.new("RGB", size, color)


# The usable palette colors (index 4 is a duplicate black, skip it).
_USABLE_COLORS = {PALETTE_RGB[i] for i in (0, 1, 2, 3, 5, 6)}


class TestDitherToPalette:
    def test_pure_black_maps_to_black(self) -> None:
        result = dither_to_palette(_solid((0, 0, 0)))
        rgb = result.convert("RGB")
        colors = rgb.getcolors()
        assert colors is not None
        assert len(colors) == 1
        assert colors[0][1] == (0, 0, 0)

    def test_pure_white_maps_to_white(self) -> None:
        result = dither_to_palette(_solid((255, 255, 255)))
        rgb = result.convert("RGB")
        colors = rgb.getcolors()
        assert colors is not None
        assert len(colors) == 1
        assert colors[0][1] == (255, 255, 255)

    def test_pure_red_maps_to_red(self) -> None:
        result = dither_to_palette(_solid((255, 0, 0)))
        rgb = result.convert("RGB")
        colors = rgb.getcolors()
        assert colors is not None
        assert len(colors) == 1
        assert colors[0][1] == (255, 0, 0)

    def test_output_mode_is_paletted(self) -> None:
        result = dither_to_palette(_solid((128, 128, 128)))
        assert result.mode == "P"

    def test_dimensions_preserved(self) -> None:
        src = _solid((100, 200, 50), size=(800, 480))
        result = dither_to_palette(src)
        assert result.size == (800, 480)

    def test_output_only_contains_palette_colors(self) -> None:
        """A gradient image, after dithering, should only use palette colors."""
        img = Image.new("RGB", (100, 100))
        # Fill with a diagonal gradient
        pixels = img.load()
        assert pixels is not None
        for x in range(100):
            for y in range(100):
                pixels[x, y] = (x * 2, y * 2, (x + y))
        result = dither_to_palette(img)
        rgb = result.convert("RGB")
        colors = rgb.getcolors(maxcolors=256)
        assert colors is not None
        for _count, color in colors:
            assert color in _USABLE_COLORS, f"Unexpected color {color} not in palette"
