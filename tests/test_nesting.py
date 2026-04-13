"""Tests for deeply nested layouts."""
import pytest
from picolay import Box, Style, render
from picolay.layout import compute_layout


def _child(w, h, **kw):
    return Box(style=Style(width=w, height=h, **kw))


class TestNesting:
    def test_two_level_nesting(self):
        root = Box(
            style=Style(width=200, height=100, flex_direction="row"),
            children=[
                Box(
                    style=Style(width=100, height=100, flex_direction="column"),
                    children=[_child(50, 30, background=(255, 0, 0)), _child(50, 30, background=(0, 255, 0))],
                ),
                Box(
                    style=Style(width=100, height=100, flex_direction="column"),
                    children=[_child(50, 30, background=(0, 0, 255))],
                ),
            ],
        )
        layout = compute_layout(root, 200, 100)
        # First column at x=0, second at x=100
        assert layout.children[0].x == 0
        assert layout.children[1].x == 100
        # Children within first column
        assert layout.children[0].children[0].y == 0
        assert layout.children[0].children[1].y == 30

    def test_three_level_nesting(self):
        inner_row = Box(
            style=Style(width=80, height=20, flex_direction="row"),
            children=[_child(20, 20), _child(20, 20)],
        )
        col = Box(
            style=Style(width=80, height=60, flex_direction="column"),
            children=[inner_row, _child(80, 20)],
        )
        root = Box(
            style=Style(width=200, height=60, flex_direction="row"),
            children=[col, _child(60, 60)],
        )
        layout = compute_layout(root, 200, 60)
        # Inner row children
        inner_children = layout.children[0].children[0].children
        assert inner_children[0].x == 0
        assert inner_children[1].x == 20

    def test_nested_padding_accumulates(self):
        inner = _child(50, 50, background=(255, 0, 0))
        mid = Box(
            style=Style(width=70, height=70, padding=5, flex_direction="row"),
            children=[inner],
        )
        root = Box(
            style=Style(width=100, height=100, padding=10, flex_direction="row", background=(255, 255, 255)),
            children=[mid],
        )
        img = render(root, 100, 100)
        # Inner content at 10 (outer pad) + 5 (inner pad) = 15
        assert img.getpixel((20, 20)) == (255, 0, 0)
        # Outer padding area
        assert img.getpixel((5, 5)) == (255, 255, 255)

    def test_nested_flex_grow(self):
        root = Box(
            style=Style(width=200, height=100, flex_direction="row"),
            children=[
                Box(
                    style=Style(height=100, flex_grow=1, flex_direction="column"),
                    children=[
                        Box(style=Style(width=100, flex_grow=1, background=(255, 0, 0))),
                        Box(style=Style(width=100, flex_grow=1, background=(0, 255, 0))),
                    ],
                ),
                Box(
                    style=Style(height=100, flex_grow=1, flex_direction="column"),
                    children=[
                        Box(style=Style(width=100, flex_grow=1, background=(0, 0, 255))),
                    ],
                ),
            ],
        )
        layout = compute_layout(root, 200, 100)
        # Each top-level child gets 100px wide
        assert abs(layout.children[0].width - 100) <= 1
        assert abs(layout.children[1].width - 100) <= 1
        # Inner children split height
        inner = layout.children[0].children
        assert abs(inner[0].height - 50) <= 1
        assert abs(inner[1].height - 50) <= 1

    def test_hero_grid_layout(self):
        """Layout matching bird-listener grid: top row (side+hero+side), bottom 3 cols."""
        top_row = Box(
            style=Style(flex_grow=0.65, flex_direction="row"),
            children=[
                Box(style=Style(flex_grow=1, background=(200, 200, 200))),  # side
                Box(style=Style(flex_grow=2, background=(150, 150, 150))),  # hero
                Box(style=Style(flex_grow=1, background=(200, 200, 200))),  # side
            ],
        )
        bottom_row = Box(
            style=Style(flex_grow=0.35, flex_direction="row"),
            children=[
                Box(style=Style(flex_grow=1, background=(180, 180, 180))),
                Box(style=Style(flex_grow=1, background=(160, 160, 160))),
                Box(style=Style(flex_grow=1, background=(140, 140, 140))),
            ],
        )
        root = Box(
            style=Style(width=300, height=200, flex_direction="column"),
            children=[top_row, bottom_row],
        )
        layout = compute_layout(root, 300, 200)
        # Top row and bottom row exist
        assert len(layout.children) == 2
        # Hero (center of top row) should be wider than sides
        top = layout.children[0]
        assert top.children[1].width > top.children[0].width

    def test_nested_alignment(self):
        inner = Box(
            style=Style(width=80, height=60, flex_direction="row", align_items="end"),
            children=[_child(20, 20)],
        )
        root = Box(
            style=Style(width=200, height=100, flex_direction="row", align_items="center"),
            children=[inner],
        )
        layout = compute_layout(root, 200, 100)
        # Inner box centered in outer (y = (100-60)/2 = 20)
        assert layout.children[0].y == 20
        # Child inside inner is end-aligned (y = 60-20 = 40 relative to inner)
        assert layout.children[0].children[0].y == 40

    def test_deep_nesting_10_levels(self):
        node = _child(60, 60, background=(255, 0, 0))
        for _ in range(10):
            node = Box(
                style=Style(padding=2, flex_direction="row"),
                children=[node],
            )
        # Set explicit size on root
        root_style = Style(width=100, height=100, padding=2, flex_direction="row")
        node = Box(style=root_style, children=node.children)
        # Re-wrap with known size
        layout = compute_layout(node, 100, 100)
        # The innermost box should be offset by ~2*10 = 20 from each side
        # Navigate to the deepest child
        current = layout
        depth = 0
        while current.children:
            current = current.children[0]
            depth += 1
        assert depth >= 10

    def test_mixed_row_and_column(self):
        root = Box(
            style=Style(width=200, height=200, flex_direction="row"),
            children=[
                Box(
                    style=Style(width=100, height=200, flex_direction="column"),
                    children=[_child(50, 50), _child(50, 50)],
                ),
                Box(
                    style=Style(width=100, height=200, flex_direction="row"),
                    children=[_child(40, 40), _child(40, 40)],
                ),
            ],
        )
        layout = compute_layout(root, 200, 200)
        # Column children stacked vertically
        col_children = layout.children[0].children
        assert col_children[0].y == 0
        assert col_children[1].y == 50
        # Row children placed horizontally
        row_children = layout.children[1].children
        assert row_children[0].x == 0
        assert row_children[1].x == 40
