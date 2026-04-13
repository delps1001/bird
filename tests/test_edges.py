"""Tests for edge cases and degenerate inputs."""
import pytest
from picolay import Box, Style, render
from picolay.layout import compute_layout


def _child(w, h, **kw):
    return Box(style=Style(width=w, height=h, **kw))


class TestEdgeCases:
    def test_zero_width_canvas(self):
        box = Box(style=Style(width=0, height=100, background=(255, 0, 0)))
        img = render(box, 0, 100)
        assert img.size == (0, 100)

    def test_zero_height_canvas(self):
        box = Box(style=Style(width=100, height=0, background=(255, 0, 0)))
        img = render(box, 100, 0)
        assert img.size == (100, 0)

    def test_box_with_no_children(self):
        box = Box(style=Style(width=50, height=50, background=(0, 255, 0)))
        img = render(box, 100, 100)
        assert img.getpixel((25, 25)) == (0, 255, 0)

    def test_box_with_no_style(self):
        box = Box()
        img = render(box, 100, 100)
        assert img.size == (100, 100)

    def test_children_exceed_parent_size(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row"),
            children=[_child(50, 50), _child(50, 50), _child(50, 50)],
        )
        # Should not crash even though 150 > 100
        img = render(parent, 100, 100)
        assert img.size == (100, 100)

    def test_overflow_hidden_clips_children(self):
        child = _child(80, 80, background=(255, 0, 0))
        parent = Box(
            style=Style(width=50, height=50, overflow="hidden", background=(255, 255, 255)),
            children=[child],
        )
        img = render(parent, 100, 100)
        # Inside parent bounds: red
        assert img.getpixel((25, 25)) == (255, 0, 0)
        # Outside parent bounds: white (canvas bg)
        assert img.getpixel((60, 60)) == (255, 255, 255)

    def test_overflow_visible_does_not_clip(self):
        child = _child(80, 80, background=(255, 0, 0))
        parent = Box(
            style=Style(width=50, height=50, overflow="visible", background=(200, 200, 200)),
            children=[child],
        )
        img = render(parent, 100, 100)
        # Child extends beyond parent - should be visible
        assert img.getpixel((60, 60)) == (255, 0, 0)

    def test_negative_margin_allowed(self):
        child = _child(50, 50, margin=-5, background=(255, 0, 0))
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", background=(255, 255, 255)),
            children=[child],
        )
        layout = compute_layout(parent, 100, 100)
        # Negative margin shifts child closer to edge
        assert layout.children[0].x == -5
        assert layout.children[0].y == -5

    def test_very_large_padding(self):
        box = Box(style=Style(width=50, height=50, padding=100))
        # Content area would be negative -> clamped to 0
        layout = compute_layout(box, 50, 50)
        assert layout.width == 50
        # Should not crash
        img = render(box, 50, 50)
        assert img.size == (50, 50)

    def test_fractional_width_and_height(self):
        box = Box(style=Style(width=0.5, height=0.5, background=(255, 0, 0)))
        img = render(box, 200, 200)
        # Box should be 100x100
        assert img.getpixel((50, 50)) == (255, 0, 0)
        assert img.getpixel((150, 150)) == (255, 255, 255)

    def test_fractional_sizing_nested(self):
        child = Box(style=Style(width=0.5, height=0.5, background=(255, 0, 0)))
        parent = Box(
            style=Style(width=0.5, height=0.5, flex_direction="row"),
            children=[child],
        )
        img = render(parent, 200, 200)
        # Parent is 100x100, child is 50x50
        assert img.getpixel((25, 25)) == (255, 0, 0)
        assert img.getpixel((75, 75)) == (255, 255, 255)

    def test_one_pixel_canvas(self):
        box = Box(style=Style(width=1, height=1, background=(255, 0, 0)))
        img = render(box, 1, 1)
        assert img.size == (1, 1)
        assert img.getpixel((0, 0)) == (255, 0, 0)

    def test_single_child_flex_grow(self):
        parent = Box(
            style=Style(width=200, height=50, flex_direction="row"),
            children=[Box(style=Style(height=50, flex_grow=1))],
        )
        layout = compute_layout(parent, 200, 50)
        assert layout.children[0].width == 200

    def test_all_children_have_flex_grow(self):
        parent = Box(
            style=Style(width=300, height=50, flex_direction="row"),
            children=[
                Box(style=Style(height=50, flex_grow=1)),
                Box(style=Style(height=50, flex_grow=1)),
                Box(style=Style(height=50, flex_grow=1)),
            ],
        )
        layout = compute_layout(parent, 300, 50)
        for c in layout.children:
            assert abs(c.width - 100) <= 1

    def test_min_width_prevents_shrinking(self):
        parent = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[
                _child(30, 50),
                _child(30, 50),
                Box(style=Style(width=30, height=50, min_width=80)),
            ],
        )
        layout = compute_layout(parent, 100, 50)
        # Third child should be at least 80px
        assert layout.children[2].width >= 80

    def test_min_height_prevents_shrinking(self):
        parent = Box(
            style=Style(width=50, height=100, flex_direction="column"),
            children=[
                _child(50, 30),
                _child(50, 30),
                Box(style=Style(width=50, height=30, min_height=80)),
            ],
        )
        layout = compute_layout(parent, 50, 100)
        assert layout.children[2].height >= 80
