"""Tests for Img node rendering and object-fit modes."""
import pytest
import tempfile
from pathlib import Path
from PIL import Image
from picolay import Box, Img, Style, render


def _solid_image(w, h, color=(255, 0, 0, 255)):
    """Create a solid color RGBA image."""
    return Image.new("RGBA", (w, h), color)


class TestImgRendering:
    def test_img_renders_pixels(self):
        src = _solid_image(32, 32, (255, 0, 0, 255))
        node = Img(src=src, style=Style(width=32, height=32))
        root = Box(
            style=Style(width=100, height=100, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 100, 100)
        # Should have red pixels from the image
        assert img.getpixel((16, 16))[0] > 200

    def test_img_contain_preserves_aspect_ratio(self):
        src = _solid_image(100, 50, (255, 0, 0, 255))
        node = Img(src=src, style=Style(width=50, height=50, object_fit="contain"))
        root = Box(
            style=Style(width=100, height=100, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 100, 100)
        # Image should be scaled to 50x25, centered vertically in 50px box
        # Top of box at y=0, image at roughly y=12
        # Center of image area should be red
        assert img.getpixel((25, 18))[0] > 200
        # Above the image (top of box) should be white
        assert img.getpixel((25, 2)) == (255, 255, 255)

    def test_img_contain_tall_image(self):
        src = _solid_image(50, 100, (0, 255, 0, 255))
        node = Img(src=src, style=Style(width=50, height=50, object_fit="contain"))
        root = Box(
            style=Style(width=100, height=100, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 100, 100)
        # Scaled to 25x50, centered horizontally
        assert img.getpixel((18, 25))[1] > 200

    def test_img_cover_fills_box(self):
        src = _solid_image(100, 50, (255, 0, 0, 255))
        node = Img(src=src, style=Style(width=50, height=50, object_fit="cover"))
        root = Box(
            style=Style(width=100, height=100, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 100, 100)
        # Entire 50x50 box should be filled with red (no white gaps)
        for x in [5, 25, 45]:
            for y in [5, 25, 45]:
                assert img.getpixel((x, y))[0] > 200

    def test_img_fill_stretches(self):
        src = _solid_image(100, 50, (0, 0, 255, 255))
        node = Img(src=src, style=Style(width=50, height=50, object_fit="fill"))
        root = Box(
            style=Style(width=100, height=100, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 100, 100)
        # All within the 50x50 box should be blue
        assert img.getpixel((25, 25))[2] > 200

    def test_img_in_flex_layout(self):
        src1 = _solid_image(30, 30, (255, 0, 0, 255))
        src2 = _solid_image(30, 30, (0, 255, 0, 255))
        root = Box(
            style=Style(width=200, height=50, flex_direction="row", background=(255, 255, 255)),
            children=[
                Img(src=src1, style=Style(width=30, height=30)),
                Img(src=src2, style=Style(width=30, height=30)),
            ],
        )
        img = render(root, 200, 50)
        # First image at x=0..30, second at x=30..60
        assert img.getpixel((15, 15))[0] > 200  # red
        assert img.getpixel((45, 15))[1] > 200  # green

    def test_img_with_border_and_padding(self):
        src = _solid_image(50, 50, (255, 0, 0, 255))
        node = Img(src=src, style=Style(width=70, height=70, object_fit="fill"))
        root = Box(
            style=Style(width=80, height=80, border=(2, (0, 0, 0)), padding=5, background=(200, 200, 200)),
            children=[node],
        )
        img = render(root, 100, 100)
        # Border pixel
        assert img.getpixel((0, 0)) == (0, 0, 0)
        # Image should be inside content area (after border+padding = 7)
        assert img.getpixel((10, 10))[0] > 100

    def test_img_rgba_transparency(self):
        # Semi-transparent red on white background
        src = Image.new("RGBA", (30, 30), (255, 0, 0, 128))
        node = Img(src=src, style=Style(width=30, height=30))
        root = Box(
            style=Style(width=50, height=50, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 50, 50)
        # Pixel should be blended (pinkish, not pure red)
        p = img.getpixel((15, 15))
        assert p[0] > 200  # red channel high
        assert p[1] > 50  # green shows through from white bg

    def test_img_from_path(self):
        src = _solid_image(20, 20, (0, 0, 255, 255))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            src.save(f, "PNG")
            path = Path(f.name)
        try:
            node = Img(src=path, style=Style(width=20, height=20))
            root = Box(
                style=Style(width=50, height=50, background=(255, 255, 255)),
                children=[node],
            )
            img = render(root, 50, 50)
            assert img.getpixel((10, 10))[2] > 200
        finally:
            path.unlink()

    def test_img_contain_square_in_square(self):
        src = _solid_image(50, 50, (255, 0, 0, 255))
        node = Img(src=src, style=Style(width=50, height=50, object_fit="contain"))
        root = Box(
            style=Style(width=50, height=50, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 50, 50)
        # Full box should be red
        assert img.getpixel((25, 25))[0] > 200
        assert img.getpixel((5, 5))[0] > 200

    def test_img_zero_size_box(self):
        src = _solid_image(30, 30, (255, 0, 0, 255))
        node = Img(src=src, style=Style(width=0, height=0))
        root = Box(
            style=Style(width=50, height=50, background=(255, 255, 255)),
            children=[node],
        )
        # Should not crash
        img = render(root, 50, 50)
        assert img.size == (50, 50)
