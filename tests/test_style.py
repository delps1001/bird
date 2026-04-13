"""Tests for Style dataclass construction and defaults."""
import pytest
from picolay import Style


class TestStyleDefaults:
    def test_default_style_values(self):
        s = Style()
        assert s.padding == (0, 0, 0, 0)
        assert s.margin == (0, 0, 0, 0)
        assert s.border == (0, (0, 0, 0))
        assert s.background is None
        assert s.flex_direction == "row"
        assert s.justify_content == "start"
        assert s.align_items == "start"
        assert s.gap == 0
        assert s.flex_grow == 0.0
        assert s.overflow == "visible"
        assert s.width is None
        assert s.height is None

    def test_style_with_uniform_padding(self):
        s = Style(padding=10)
        assert s.padding == (10, 10, 10, 10)

    def test_style_with_per_side_padding(self):
        s = Style(padding=(5, 10, 15, 20))
        assert s.padding == (5, 10, 15, 20)
        assert s.padding_top == 5
        assert s.padding_right == 10
        assert s.padding_bottom == 15
        assert s.padding_left == 20

    def test_style_with_uniform_margin(self):
        s = Style(margin=8)
        assert s.margin == (8, 8, 8, 8)

    def test_style_with_per_side_margin(self):
        s = Style(margin=(1, 2, 3, 4))
        assert s.margin == (1, 2, 3, 4)
        assert s.margin_top == 1
        assert s.margin_right == 2
        assert s.margin_bottom == 3
        assert s.margin_left == 4

    def test_style_with_border(self):
        s = Style(border=(2, (0, 0, 0)))
        assert s.border_width == 2
        assert s.border_color == (0, 0, 0)

    def test_style_is_immutable(self):
        s = Style(padding=10)
        with pytest.raises(AttributeError):
            s.padding = (1, 1, 1, 1)
        with pytest.raises(AttributeError):
            s.flex_direction = "column"

    def test_style_padding_two_value_shorthand(self):
        s = Style(padding=(10, 20))
        assert s.padding == (10, 20, 10, 20)

    def test_style_margin_two_value_shorthand(self):
        s = Style(margin=(5, 15))
        assert s.margin == (5, 15, 5, 15)
