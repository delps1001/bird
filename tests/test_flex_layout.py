"""Tests for flexbox layout: direction, alignment, gap, grow."""
import pytest
from picolay import Box, Style, render
from picolay.layout import compute_layout


def _child(w, h, **kw):
    return Box(style=Style(width=w, height=h, **kw))


def _positions(layout):
    """Return list of (x, y, w, h) for each child in layout."""
    return [(int(c.x), int(c.y), int(c.width), int(c.height)) for c in layout.children]


class TestFlexDirection:
    def test_flex_row_places_children_horizontally(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row"),
            children=[_child(30, 30), _child(30, 30), _child(30, 30)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert pos[0][:2] == (0, 0)
        assert pos[1][:2] == (30, 0)
        assert pos[2][:2] == (60, 0)

    def test_flex_column_places_children_vertically(self):
        parent = Box(
            style=Style(width=100, height=200, flex_direction="column"),
            children=[_child(30, 30), _child(30, 30), _child(30, 30)],
        )
        layout = compute_layout(parent, 100, 200)
        pos = _positions(layout)
        assert pos[0][:2] == (0, 0)
        assert pos[1][:2] == (0, 30)
        assert pos[2][:2] == (0, 60)


class TestGap:
    def test_flex_row_with_gap(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", gap=10),
            children=[_child(30, 30), _child(30, 30), _child(30, 30)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert pos[0][0] == 0
        assert pos[1][0] == 40
        assert pos[2][0] == 80

    def test_flex_column_with_gap(self):
        parent = Box(
            style=Style(width=100, height=200, flex_direction="column", gap=10),
            children=[_child(30, 30), _child(30, 30), _child(30, 30)],
        )
        layout = compute_layout(parent, 100, 200)
        pos = _positions(layout)
        assert pos[0][1] == 0
        assert pos[1][1] == 40
        assert pos[2][1] == 80

    def test_gap_with_single_child(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", gap=10),
            children=[_child(30, 30)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert pos[0][0] == 0


class TestJustifyContent:
    def test_justify_start(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="start"),
            children=[_child(20, 20), _child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        assert pos[0][0] == 0
        assert pos[1][0] == 20
        assert pos[2][0] == 40

    def test_justify_center(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="center"),
            children=[_child(20, 20), _child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        assert pos[0][0] == 20

    def test_justify_end(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="end"),
            children=[_child(20, 20), _child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        assert pos[0][0] == 40
        assert pos[2][0] == 80

    def test_justify_space_between(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="space_between"),
            children=[_child(20, 20), _child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        assert pos[0][0] == 0
        assert pos[1][0] == 40
        assert pos[2][0] == 80

    def test_justify_space_around(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="space_around"),
            children=[_child(20, 20), _child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        # Space = 100 - 60 = 40, slot = 40/3 ≈ 13.3, half ≈ 6.67
        assert abs(pos[0][0] - 6) <= 1
        assert abs(pos[1][0] - 40) <= 1
        assert abs(pos[2][0] - 73) <= 1

    def test_justify_space_between_two_children(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="space_between"),
            children=[_child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        assert pos[0][0] == 0
        assert pos[1][0] == 80

    def test_justify_space_between_one_child(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="space_between"),
            children=[_child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        assert pos[0][0] == 40

    def test_justify_center_in_column(self):
        parent = Box(
            style=Style(width=100, height=100, flex_direction="column", justify_content="center"),
            children=[_child(20, 20), _child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        assert pos[0][1] == 20

    def test_justify_with_gap(self):
        """space_between with gap: gap acts as minimum spacing."""
        parent = Box(
            style=Style(width=100, height=100, flex_direction="row", justify_content="space_between", gap=5),
            children=[_child(20, 20), _child(20, 20), _child(20, 20)],
        )
        layout = compute_layout(parent, 100, 100)
        pos = _positions(layout)
        # space_between distributes 40px of space between 2 gaps = 20px each
        # gap doesn't add extra since space_between already exceeds gap
        assert pos[0][0] == 0
        assert pos[1][0] == 40
        assert pos[2][0] == 80


class TestAlignItems:
    def test_align_start(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", align_items="start"),
            children=[_child(30, 20), _child(30, 40), _child(30, 30)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert all(p[1] == 0 for p in pos)

    def test_align_center(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", align_items="center"),
            children=[_child(30, 40)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert pos[0][1] == 30

    def test_align_end(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", align_items="end"),
            children=[_child(30, 40)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert pos[0][1] == 60

    def test_align_stretch(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", align_items="stretch"),
            children=[Box(style=Style(width=30))],  # no height
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert pos[0][3] == 100  # height stretched to parent

    def test_align_stretch_does_not_override_fixed_height(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", align_items="stretch"),
            children=[_child(30, 40)],  # has explicit height
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        assert pos[0][3] == 40

    def test_align_center_in_column(self):
        parent = Box(
            style=Style(width=100, height=200, flex_direction="column", align_items="center"),
            children=[_child(40, 30)],
        )
        layout = compute_layout(parent, 100, 200)
        pos = _positions(layout)
        assert pos[0][0] == 30


class TestFlexGrow:
    def test_flex_grow_fills_remaining_space(self):
        parent = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[
                _child(30, 50),
                Box(style=Style(height=50, flex_grow=1)),
            ],
        )
        layout = compute_layout(parent, 100, 50)
        pos = _positions(layout)
        assert pos[0][2] == 30
        assert pos[1][2] == 70

    def test_flex_grow_proportional(self):
        parent = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[
                Box(style=Style(height=50, flex_grow=1)),
                Box(style=Style(height=50, flex_grow=2)),
            ],
        )
        layout = compute_layout(parent, 100, 50)
        pos = _positions(layout)
        assert abs(pos[0][2] - 33) <= 1
        assert abs(pos[1][2] - 67) <= 1

    def test_flex_grow_with_fixed_and_growing(self):
        parent = Box(
            style=Style(width=200, height=50, flex_direction="row"),
            children=[
                _child(50, 50),
                Box(style=Style(height=50, flex_grow=1)),
                Box(style=Style(height=50, flex_grow=3)),
            ],
        )
        layout = compute_layout(parent, 200, 50)
        pos = _positions(layout)
        assert pos[0][2] == 50
        assert abs(pos[1][2] - 37) <= 1
        assert abs(pos[2][2] - 113) <= 1

    def test_flex_grow_in_column(self):
        parent = Box(
            style=Style(width=50, height=100, flex_direction="column"),
            children=[
                _child(50, 20),
                Box(style=Style(width=50, flex_grow=1)),
            ],
        )
        layout = compute_layout(parent, 50, 100)
        pos = _positions(layout)
        assert pos[0][3] == 20
        assert pos[1][3] == 80

    def test_flex_grow_zero_has_no_effect(self):
        parent = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[_child(30, 50), _child(30, 50)],
        )
        layout = compute_layout(parent, 100, 50)
        pos = _positions(layout)
        assert pos[0][2] == 30
        assert pos[1][2] == 30

    def test_flex_grow_with_gap(self):
        parent = Box(
            style=Style(width=100, height=50, flex_direction="row", gap=10),
            children=[
                Box(style=Style(height=50, flex_grow=1)),
                Box(style=Style(height=50, flex_grow=1)),
            ],
        )
        layout = compute_layout(parent, 100, 50)
        pos = _positions(layout)
        assert abs(pos[0][2] - 45) <= 1
        assert abs(pos[1][2] - 45) <= 1


class TestCombined:
    def test_justify_center_with_gap(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", justify_content="center", gap=10),
            children=[_child(30, 30), _child(30, 30)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        # Total = 30+30+10 = 70, centered in 200 → start at 65
        assert abs(pos[0][0] - 65) <= 1

    def test_row_with_padding_and_gap(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", padding=10, gap=5),
            children=[_child(30, 30), _child(30, 30), _child(30, 30)],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        # Children start at padding_left=10
        assert pos[0][0] == 10
        assert pos[1][0] == 45  # 10 + 30 + 5
        assert pos[2][0] == 80  # 10 + 30 + 5 + 30 + 5

    def test_column_with_margin_children(self):
        parent = Box(
            style=Style(width=100, height=200, flex_direction="column"),
            children=[
                _child(50, 30, margin=5),
                _child(50, 30, margin=5),
            ],
        )
        layout = compute_layout(parent, 100, 200)
        pos = _positions(layout)
        # First child: y = margin_top=5
        assert pos[0][1] == 5
        # Second child: y = 5 + 30 + 5(margin_bottom) + 5(margin_top) = 45
        # Actually margin_top + height + margin_bottom = 5+30+5 = 40
        assert pos[1][1] == 45

    def test_mixed_fixed_and_grow_with_padding(self):
        parent = Box(
            style=Style(width=200, height=100, flex_direction="row", padding=10),
            children=[
                _child(50, 50),
                Box(style=Style(height=50, flex_grow=1)),
            ],
        )
        layout = compute_layout(parent, 200, 100)
        pos = _positions(layout)
        # Content width = 200 - 20 = 180
        assert pos[0][2] == 50
        assert pos[1][2] == 130  # 180 - 50
