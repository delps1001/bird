"""Tests for Text node rendering, alignment, and sizing."""
import pytest
from PIL import Image
from picolay import Box, Text, Style, render
from picolay.layout import compute_layout


class TestTextRendering:
    def test_text_renders_non_blank(self):
        node = Text("Hello", style=Style(font_size=20, font_color=(0, 0, 0)))
        root = Box(
            style=Style(width=200, height=50, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 200, 50)
        # Should have some non-white pixels
        pixels = list(img.getdata())
        assert any(p != (255, 255, 255) for p in pixels)

    def test_text_color(self):
        node = Text("Hello", style=Style(font_size=20, font_color=(255, 0, 0)))
        root = Box(
            style=Style(width=200, height=50, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 200, 50)
        pixels = list(img.getdata())
        # Should have some reddish pixels
        assert any(p[0] > 200 and p[1] < 50 and p[2] < 50 for p in pixels)

    def test_text_align_left(self):
        node = Text("Hi", style=Style(width=200, height=30, font_size=16, text_align="left"))
        root = Box(
            style=Style(width=200, height=30, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 200, 30)
        # Left side should have dark pixels (text)
        left_col = [img.getpixel((5, y)) for y in range(30)]
        right_col = [img.getpixel((195, y)) for y in range(30)]
        left_dark = sum(1 for p in left_col if p[0] < 128)
        right_dark = sum(1 for p in right_col if p[0] < 128)
        # Left should have more dark pixels than right
        assert left_dark >= right_dark

    def test_text_align_center(self):
        node = Text("X", style=Style(width=200, height=30, font_size=16, text_align="center"))
        root = Box(
            style=Style(width=200, height=30, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 200, 30)
        # Center region should have text
        center_region = [img.getpixel((x, 15)) for x in range(80, 120)]
        has_dark = any(p[0] < 200 for p in center_region)
        assert has_dark

    def test_text_align_right(self):
        node = Text("Hi", style=Style(width=200, height=30, font_size=16, text_align="right"))
        root = Box(
            style=Style(width=200, height=30, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 200, 30)
        # Right side should have text
        right_region = [img.getpixel((x, 15)) for x in range(160, 200)]
        left_region = [img.getpixel((x, 15)) for x in range(0, 40)]
        right_dark = sum(1 for p in right_region if p[0] < 200)
        left_dark = sum(1 for p in left_region if p[0] < 200)
        assert right_dark >= left_dark

    def test_text_font_size_affects_height(self):
        t1 = Text("Hello", style=Style(font_size=10))
        t2 = Text("Hello", style=Style(font_size=30))
        l1 = compute_layout(t1, 200, 200)
        l2 = compute_layout(t2, 200, 200)
        assert l2.height > l1.height

    def test_text_intrinsic_size(self):
        node = Text("Hello World", style=Style(font_size=16))
        layout = compute_layout(node, 500, 500)
        assert layout.width > 0
        assert layout.height > 0

    def test_text_in_flex_row(self):
        root = Box(
            style=Style(width=400, height=50, flex_direction="row", background=(255, 255, 255)),
            children=[
                Text("AAA", style=Style(font_size=16)),
                Text("BBB", style=Style(font_size=16)),
            ],
        )
        layout = compute_layout(root, 400, 50)
        # Second text should be to the right of first
        assert layout.children[1].x > layout.children[0].x

    def test_text_with_explicit_width_truncates(self):
        node = Text(
            "This is a very long text string",
            style=Style(width=50, height=30, font_size=16),
        )
        root = Box(
            style=Style(width=50, height=30, background=(255, 255, 255), overflow="hidden"),
            children=[node],
        )
        img = render(root, 200, 200)
        # Should not crash; image should be valid
        assert img.size == (200, 200)

    def test_empty_text_renders_nothing(self):
        node = Text("", style=Style(font_size=16))
        root = Box(
            style=Style(width=100, height=30, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 100, 30)
        # All pixels should be white (background only)
        pixels = list(img.getdata())
        assert all(p == (255, 255, 255) for p in pixels)

    def test_text_vertical_center_in_parent(self):
        root = Box(
            style=Style(width=200, height=100, flex_direction="row", align_items="center", background=(255, 255, 255)),
            children=[Text("Hi", style=Style(font_size=16))],
        )
        layout = compute_layout(root, 200, 100)
        child_y = layout.children[0].y
        child_h = layout.children[0].height
        # Should be roughly centered
        assert abs((child_y + child_h / 2) - 50) < 20

    def test_text_respects_parent_padding(self):
        root = Box(
            style=Style(width=200, height=100, padding=20, flex_direction="row", background=(255, 255, 255)),
            children=[Text("Hello", style=Style(font_size=16, font_color=(0, 0, 0)))],
        )
        img = render(root, 200, 100)
        # Left padding area (0-19) should be white
        left_pad = [img.getpixel((5, y)) for y in range(20, 80)]
        assert all(p == (255, 255, 255) for p in left_pad)

    def test_text_with_font_fallback(self):
        # Use a non-existent font path
        node = Text("Test", style=Style(font_size=16))
        root = Box(
            style=Style(width=100, height=30, background=(255, 255, 255)),
            children=[node],
        )
        img = render(root, 100, 30)
        # Should not crash, should produce some visible text
        pixels = list(img.getdata())
        assert any(p != (255, 255, 255) for p in pixels)
