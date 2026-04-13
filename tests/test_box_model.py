"""Tests for box model: padding, margin, border sizing."""
import pytest
from PIL import Image
from picolay import Box, Style, render


class TestBoxModel:
    def test_box_fixed_size_renders_exact_dimensions(self):
        box = Box(style=Style(width=100, height=50, background=(255, 0, 0)))
        img = render(box, 200, 200)
        # Red rectangle at top-left
        assert img.getpixel((50, 25)) == (255, 0, 0)
        # Outside the box is white
        assert img.getpixel((150, 100)) == (255, 255, 255)

    def test_box_with_padding_shrinks_content_area(self):
        child = Box(style=Style(width=80, height=80, background=(0, 0, 255)))
        parent = Box(
            style=Style(width=100, height=100, padding=10, background=(255, 0, 0)),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Inside padding: child at (10,10)
        assert img.getpixel((15, 15)) == (0, 0, 255)
        # Padding area shows parent background
        assert img.getpixel((5, 5)) == (255, 0, 0)

    def test_box_with_per_side_padding(self):
        child = Box(style=Style(width=70, height=80, background=(0, 0, 255)))
        parent = Box(
            style=Style(width=100, height=100, padding=(5, 10, 15, 20), background=(255, 0, 0)),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Child starts at (left=20, top=5)
        assert img.getpixel((25, 8)) == (0, 0, 255)
        # Left padding area
        assert img.getpixel((10, 50)) == (255, 0, 0)

    def test_box_with_margin_offsets_position(self):
        child = Box(style=Style(width=70, height=70, margin=10, background=(0, 255, 0)))
        parent = Box(
            style=Style(width=100, height=100, background=(255, 0, 0)),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Child at (10, 10) due to margin
        assert img.getpixel((15, 15)) == (0, 255, 0)
        # Margin area shows parent
        assert img.getpixel((5, 5)) == (255, 0, 0)

    def test_box_with_per_side_margin(self):
        child = Box(style=Style(width=60, height=60, margin=(5, 10, 15, 20), background=(0, 255, 0)))
        parent = Box(
            style=Style(width=100, height=100, background=(255, 0, 0)),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Child at (left=20, top=5)
        assert img.getpixel((25, 8)) == (0, 255, 0)

    def test_border_renders_around_box(self):
        box = Box(style=Style(width=100, height=100, border=(3, (0, 0, 0)), background=(200, 200, 200)))
        img = render(box, 200, 200)
        # Corners should be black (border)
        assert img.getpixel((0, 0)) == (0, 0, 0)
        assert img.getpixel((99, 0)) == (0, 0, 0)
        assert img.getpixel((0, 99)) == (0, 0, 0)
        assert img.getpixel((99, 99)) == (0, 0, 0)
        # Inside border should be background
        assert img.getpixel((3, 3)) == (200, 200, 200)

    def test_border_reduces_content_area(self):
        child = Box(style=Style(width=86, height=86, background=(0, 0, 255)))
        parent = Box(
            style=Style(width=100, height=100, border=(2, (0, 0, 0)), padding=5, background=(200, 200, 200)),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Content starts at border(2) + padding(5) = 7
        assert img.getpixel((10, 10)) == (0, 0, 255)
        # Border pixel
        assert img.getpixel((0, 0)) == (0, 0, 0)

    def test_padding_plus_margin_plus_border(self):
        child = Box(style=Style(width=50, height=50, margin=10, background=(0, 255, 0)))
        parent = Box(
            style=Style(width=200, height=200, border=(3, (0, 0, 0)), padding=5, background=(200, 200, 200)),
            children=[child],
        )
        img = render(parent, 300, 300)
        # Child at margin(10) + border(3) + padding(5) = 18 from parent origin
        assert img.getpixel((22, 22)) == (0, 255, 0)

    def test_background_color_fills_border_box(self):
        box = Box(style=Style(width=100, height=100, padding=10, background=(0, 255, 0)))
        img = render(box, 200, 200)
        # Background fills whole box including padding area
        assert img.getpixel((5, 5)) == (0, 255, 0)
        assert img.getpixel((50, 50)) == (0, 255, 0)

    def test_no_background_is_transparent(self):
        child = Box(style=Style(width=50, height=50))  # no background
        parent = Box(
            style=Style(width=100, height=100, background=(255, 0, 0)),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Child area shows parent background since child has no bg
        assert img.getpixel((25, 25)) == (255, 0, 0)

    def test_box_with_zero_padding(self):
        child = Box(style=Style(width=100, height=100, background=(0, 0, 255)))
        parent = Box(
            style=Style(width=100, height=100, padding=0, background=(255, 0, 0)),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Child at (0,0)
        assert img.getpixel((0, 0)) == (0, 0, 255)

    def test_box_larger_than_canvas(self):
        box = Box(style=Style(width=500, height=500, background=(255, 0, 0)))
        # Should not crash
        img = render(box, 100, 100)
        assert img.size == (100, 100)
        assert img.getpixel((50, 50)) == (255, 0, 0)
