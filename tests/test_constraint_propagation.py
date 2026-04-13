"""Tests for width constraint propagation in picolay layout engine."""
from PIL import Image
from picolay import Box, Text, Img, Style, render
from picolay.layout import compute_layout


def _long_text(font_size=20):
    """Return a Text node with content wide enough to exceed typical containers."""
    return Text("Very long species name here that should be truncated", style=Style(font_size=font_size))


def _solid_image(w, h, color=(255, 0, 0, 255)):
    """Create a solid color RGBA image."""
    return Image.new("RGBA", (w, h), color)


# ---------------------------------------------------------------------------
# Category 1: Text Constrained by Parent Width (Row)
# ---------------------------------------------------------------------------

class TestTextCappedInRow:
    def test_text_caps_to_parent_width_in_row(self):
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[_long_text(font_size=20)],
        )
        layout = compute_layout(root, 100, 50)
        text_layout = layout.children[0]
        assert text_layout.width <= 100

    def test_text_narrower_than_parent_is_unchanged(self):
        short = Text("Hi", style=Style(font_size=12))
        root = Box(
            style=Style(width=500, height=50, flex_direction="row"),
            children=[short],
        )
        layout = compute_layout(root, 500, 50)
        text_layout = layout.children[0]
        # Should be intrinsic size, not stretched to 500
        assert text_layout.width < 500

    def test_text_caps_to_padded_content_area(self):
        root = Box(
            style=Style(width=200, height=50, padding=20, flex_direction="row"),
            children=[_long_text()],
        )
        layout = compute_layout(root, 200, 50)
        text_layout = layout.children[0]
        # Content area is 200 - 20*2 = 160
        assert text_layout.width <= 160

    def test_text_with_explicit_width_ignores_cap(self):
        text = Text("Long text here", style=Style(width=300, font_size=20))
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 100, 50)
        text_layout = layout.children[0]
        assert text_layout.width == 300

    def test_multiple_texts_in_row_each_capped(self):
        root = Box(
            style=Style(width=200, height=50, flex_direction="row"),
            children=[_long_text(), _long_text()],
        )
        layout = compute_layout(root, 200, 50)
        for cl in layout.children:
            assert cl.width <= 200

    def test_text_in_row_with_fixed_sibling(self):
        fixed = Box(style=Style(width=100, height=30))
        root = Box(
            style=Style(width=300, height=50, flex_direction="row"),
            children=[fixed, _long_text()],
        )
        layout = compute_layout(root, 300, 50)
        text_layout = layout.children[1]
        # Text caps to available_w (parent content width), not remaining after siblings
        assert text_layout.width <= 300


# ---------------------------------------------------------------------------
# Category 2: Text Constrained by Parent Height (Column)
# ---------------------------------------------------------------------------

class TestTextCappedInColumn:
    def test_text_caps_height_in_column(self):
        text = Text("Tall", style=Style(font_size=40))
        root = Box(
            style=Style(width=200, height=50, flex_direction="column"),
            children=[text],
        )
        layout = compute_layout(root, 200, 50)
        text_layout = layout.children[0]
        assert text_layout.height <= 50

    def test_text_shorter_than_parent_is_unchanged(self):
        text = Text("Hi", style=Style(font_size=12))
        root = Box(
            style=Style(width=200, height=500, flex_direction="column"),
            children=[text],
        )
        layout = compute_layout(root, 200, 500)
        text_layout = layout.children[0]
        assert text_layout.height < 500


# ---------------------------------------------------------------------------
# Category 3: Text Inside flex_grow Containers
# ---------------------------------------------------------------------------

class TestTextInFlexGrow:
    def test_text_in_flex_grow_box_gets_parent_width(self):
        text = _long_text()
        grow_box = Box(
            style=Style(flex_grow=1, flex_direction="row"),
            children=[text],
        )
        root = Box(
            style=Style(width=400, height=50, flex_direction="row"),
            children=[
                Box(style=Style(width=100, height=30)),
                grow_box,
            ],
        )
        layout = compute_layout(root, 400, 50)
        grow_layout = layout.children[1]
        text_layout = grow_layout.children[0]
        # grow_box gets ~300px, text should be capped to that
        assert text_layout.width <= 300

    def test_text_with_flex_grow_in_row(self):
        text = Text("Short", style=Style(flex_grow=1, font_size=12))
        root = Box(
            style=Style(width=200, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 200, 50)
        text_layout = layout.children[0]
        # flex_grow=1 should give it the full 200px
        assert text_layout.width == 200


# ---------------------------------------------------------------------------
# Category 4: Text Inside Nested flex_grow Containers
# ---------------------------------------------------------------------------

class TestTextInNestedFlexGrow:
    def test_text_in_doubly_nested_grow_box(self):
        text = _long_text()
        inner = Box(style=Style(flex_direction="column"), children=[text])
        outer = Box(style=Style(flex_grow=1), children=[inner])
        root = Box(
            style=Style(width=600, height=50, flex_direction="row"),
            children=[outer],
        )
        layout = compute_layout(root, 600, 50)
        # Navigate to text
        outer_l = layout.children[0]
        inner_l = outer_l.children[0]
        text_l = inner_l.children[0]
        assert text_l.width <= 600

    def test_text_in_nested_grow_with_padding(self):
        text = _long_text()
        outer = Box(
            style=Style(flex_grow=1, padding=20, flex_direction="row"),
            children=[text],
        )
        root = Box(
            style=Style(width=400, height=80, flex_direction="row"),
            children=[outer],
        )
        layout = compute_layout(root, 400, 80)
        outer_l = layout.children[0]
        text_l = outer_l.children[0]
        # outer gets 400, content area is 400-40=360
        assert text_l.width <= 360


# ---------------------------------------------------------------------------
# Category 5: Img Constrained by Parent
# ---------------------------------------------------------------------------

class TestImgConstrained:
    def test_img_caps_to_parent_width(self):
        src = _solid_image(500, 50)
        img = Img(src=src, style=Style())
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[img],
        )
        layout = compute_layout(root, 100, 50)
        img_l = layout.children[0]
        assert img_l.width <= 100

    def test_img_caps_to_parent_height(self):
        src = _solid_image(50, 500)
        img = Img(src=src, style=Style())
        root = Box(
            style=Style(width=200, height=100, flex_direction="column"),
            children=[img],
        )
        layout = compute_layout(root, 200, 100)
        img_l = layout.children[0]
        assert img_l.height <= 100

    def test_img_smaller_than_parent_is_unchanged(self):
        src = _solid_image(30, 30)
        img = Img(src=src, style=Style())
        root = Box(
            style=Style(width=200, height=200, flex_direction="row"),
            children=[img],
        )
        layout = compute_layout(root, 200, 200)
        img_l = layout.children[0]
        assert img_l.width == 30
        assert img_l.height == 30


# ---------------------------------------------------------------------------
# Category 6: max_width / max_height
# ---------------------------------------------------------------------------

class TestMaxWidthHeight:
    def test_max_width_caps_box(self):
        box = Box(style=Style(width=200, height=50, max_width=150))
        layout = compute_layout(box, 300, 300)
        assert layout.width == 150

    def test_max_height_caps_box(self):
        box = Box(style=Style(width=100, height=200, max_height=100))
        layout = compute_layout(box, 300, 300)
        assert layout.height == 100

    def test_max_width_on_text(self):
        text = _long_text()
        root = Box(
            style=Style(width=300, height=50, flex_direction="row"),
            children=[Text("Long long text", style=Style(font_size=20, max_width=80))],
        )
        layout = compute_layout(root, 300, 50)
        text_l = layout.children[0]
        assert text_l.width <= 80

    def test_max_height_on_text(self):
        text = Text("Hi", style=Style(font_size=40, max_height=10))
        root = Box(
            style=Style(width=200, height=200, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 200, 200)
        text_l = layout.children[0]
        assert text_l.height <= 10

    def test_max_width_on_img(self):
        src = _solid_image(200, 50)
        img = Img(src=src, style=Style(max_width=50))
        root = Box(
            style=Style(width=300, height=100, flex_direction="row"),
            children=[img],
        )
        layout = compute_layout(root, 300, 100)
        img_l = layout.children[0]
        assert img_l.width <= 50

    def test_min_wins_over_max(self):
        box = Box(style=Style(width=80, height=50, max_width=50, min_width=100))
        layout = compute_layout(box, 300, 300)
        assert layout.width == 100

    def test_max_width_fractional(self):
        box = Box(style=Style(width=300, height=50, max_width=0.5))
        layout = compute_layout(box, 400, 400)
        assert layout.width <= 200

    def test_max_width_does_not_stretch(self):
        # Box with no explicit width fills available; max_width=500 shouldn't inflate beyond available
        box = Box(style=Style(height=50, max_width=500))
        layout = compute_layout(box, 300, 300)
        assert layout.width == 300

    def test_max_width_with_flex_grow(self):
        child = Box(style=Style(flex_grow=1, height=30, max_width=100))
        root = Box(
            style=Style(width=400, height=50, flex_direction="row"),
            children=[child],
        )
        layout = compute_layout(root, 400, 50)
        child_l = layout.children[0]
        assert child_l.width <= 100

    def test_max_height_with_flex_grow(self):
        child = Box(style=Style(flex_grow=1, width=30, max_height=100))
        root = Box(
            style=Style(width=200, height=400, flex_direction="column"),
            children=[child],
        )
        layout = compute_layout(root, 200, 400)
        child_l = layout.children[0]
        assert child_l.height <= 100


# ---------------------------------------------------------------------------
# Category 7: Text Clipping at Render Time
# ---------------------------------------------------------------------------

class TestTextClipping:
    def test_text_clipped_to_layout_box(self):
        text = Text("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", style=Style(width=50, font_size=20, font_color=(0, 0, 0)))
        root = Box(
            style=Style(width=200, height=50, background=(255, 255, 255)),
            children=[text],
        )
        img = render(root, 200, 50)
        # Pixels beyond x=50 should be white (no text bleed)
        for x_check in range(60, 200):
            pixel = img.getpixel((x_check, 25))
            assert pixel == (255, 255, 255), f"Pixel at ({x_check}, 25) = {pixel}, expected white"

    def test_text_fits_no_clipping_needed(self):
        text = Text("Hi", style=Style(font_size=12, font_color=(0, 0, 0)))
        root = Box(
            style=Style(width=200, height=50, background=(255, 255, 255)),
            children=[text],
        )
        img = render(root, 200, 50)
        # Should have some non-white pixels (text rendered)
        pixels = list(img.getdata())
        assert any(p != (255, 255, 255) for p in pixels)

    def test_text_clipped_with_padding(self):
        text = Text("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", style=Style(font_size=20, font_color=(0, 0, 0)))
        root = Box(
            style=Style(width=100, height=50, padding=10, background=(255, 255, 255), flex_direction="row"),
            children=[text],
        )
        img = render(root, 200, 50)
        # Content area is x=10..90 (padding=10 on each side of 100px box)
        # Pixels beyond x=90 should be white
        for x_check in range(95, 200):
            pixel = img.getpixel((x_check, 25))
            assert pixel == (255, 255, 255), f"Pixel at ({x_check}, 25) = {pixel}, expected white"

    def test_text_clipped_preserves_alignment(self):
        text = Text("ABCDEFGHIJKLMNOPQRSTUVWXYZ", style=Style(
            width=50, font_size=20, font_color=(0, 0, 0), text_align="right"
        ))
        root = Box(
            style=Style(width=200, height=50, background=(255, 255, 255)),
            children=[text],
        )
        img = render(root, 200, 50)
        # The text box is 50px wide starting at x=0
        # With right alignment, visible portion should show the right end of text
        # At minimum, no pixels should appear beyond x=50
        for x_check in range(55, 200):
            pixel = img.getpixel((x_check, 25))
            assert pixel == (255, 255, 255), f"Pixel at ({x_check}, 25) = {pixel}, expected white"

    def test_text_barely_overflowing_is_clipped(self):
        """Text a few pixels wider than container is clipped cleanly — no bleed."""
        from picolay.fonts import load_font
        font = load_font(size=30)
        bbox = font.getbbox("Red-bellied Woodpecker")
        intrinsic_w = bbox[2] - bbox[0]
        container_w = intrinsic_w - 10  # 10px narrower than intrinsic

        text = Text("Red-bellied Woodpecker", style=Style(font_size=30, font_color=(0, 0, 0)))
        root = Box(
            style=Style(width=container_w, height=50, background=(255, 255, 255),
                        flex_direction="row"),
            children=[text],
        )
        img = render(root, container_w + 100, 50, background=(255, 255, 255))
        for x in range(container_w + 5, container_w + 100):
            for y in range(0, 50):
                assert img.getpixel((x, y)) == (255, 255, 255)


# ---------------------------------------------------------------------------
# Category 8: Interaction with Existing Features
# ---------------------------------------------------------------------------

class TestInteractionWithExisting:
    def test_constrained_text_with_justify_center(self):
        text = _long_text()
        root = Box(
            style=Style(width=200, height=50, flex_direction="row", justify_content="center"),
            children=[text],
        )
        layout = compute_layout(root, 200, 50)
        text_l = layout.children[0]
        assert text_l.width <= 200
        # Should be centered: x > 0 if text is narrower than 200
        if text_l.width < 200:
            assert text_l.x > 0

    def test_constrained_text_with_align_center(self):
        text = _long_text()
        root = Box(
            style=Style(width=200, height=100, flex_direction="column", align_items="center"),
            children=[text],
        )
        layout = compute_layout(root, 200, 100)
        text_l = layout.children[0]
        assert text_l.width <= 200
        # Cross-axis centered: x > 0 if text is narrower than 200
        if text_l.width < 200:
            assert text_l.x > 0

    def test_constrained_text_with_overflow_hidden(self):
        text = _long_text()
        root = Box(
            style=Style(width=100, height=50, overflow="hidden", background=(255, 255, 255), flex_direction="row"),
            children=[text],
        )
        img = render(root, 200, 100)
        # No pixels outside the 100x50 box should have text
        for x_check in range(105, 200):
            pixel = img.getpixel((x_check, 25))
            assert pixel == (255, 255, 255), f"Pixel at ({x_check}, 25) = {pixel}"

    def test_constrained_img_with_object_fit_contain(self):
        src = _solid_image(200, 200, (255, 0, 0, 255))
        img = Img(src=src, style=Style(max_width=50, max_height=50))
        root = Box(
            style=Style(width=100, height=100, background=(255, 255, 255)),
            children=[img],
        )
        rendered = render(root, 100, 100)
        img_layout = compute_layout(root, 100, 100).children[0]
        assert img_layout.width <= 50
        assert img_layout.height <= 50

    def test_constrained_text_with_border_and_padding(self):
        text = _long_text()
        root = Box(
            style=Style(width=100, height=50, border=(3, (0, 0, 0)), padding=5, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 100, 50)
        text_l = layout.children[0]
        # Content area: 100 - 3*2 - 5*2 = 84
        assert text_l.width <= 84

    def test_constrained_text_with_margin(self):
        text = Text("Very long species name here", style=Style(font_size=20, margin=10))
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 100, 50)
        text_l = layout.children[0]
        # Available width for text = 100 - 10*2 margin = 80
        assert text_l.width <= 80


# ---------------------------------------------------------------------------
# Category 9: Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_available_width_text(self):
        text = _long_text()
        root = Box(
            style=Style(width=0, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 0, 50)
        text_l = layout.children[0]
        assert text_l.width == 0

    def test_zero_available_height_text(self):
        text = Text("Hi", style=Style(font_size=20))
        root = Box(
            style=Style(width=200, height=0, flex_direction="column"),
            children=[text],
        )
        layout = compute_layout(root, 200, 0)
        # Should not crash
        text_l = layout.children[0]
        assert text_l.height == 0

    def test_empty_text_still_zero(self):
        text = Text("", style=Style(font_size=20))
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 100, 50)
        text_l = layout.children[0]
        assert text_l.width == 0
        assert text_l.height == 0

    def test_very_large_font_in_tiny_box(self):
        text = Text("X", style=Style(font_size=100))
        root = Box(
            style=Style(width=10, height=10, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 10, 10)
        text_l = layout.children[0]
        assert text_l.width <= 10

    def test_img_zero_available_space(self):
        src = _solid_image(50, 50)
        img = Img(src=src, style=Style())
        root = Box(
            style=Style(width=0, height=0, flex_direction="row"),
            children=[img],
        )
        layout = compute_layout(root, 0, 0)
        img_l = layout.children[0]
        assert img_l.width == 0

    def test_text_with_negative_available_width(self):
        # padding > width means content area = 0
        text = _long_text()
        root = Box(
            style=Style(width=10, height=50, padding=20, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 10, 50)
        text_l = layout.children[0]
        assert text_l.width == 0

    def test_deeply_nested_constraint_propagation(self):
        text = _long_text()
        node = text
        for _ in range(5):
            node = Box(
                style=Style(flex_grow=1, padding=5, flex_direction="row"),
                children=[node],
            )
        root = Box(
            style=Style(width=300, height=100, flex_direction="row"),
            children=[node],
        )
        layout = compute_layout(root, 300, 100)
        # Navigate to innermost text
        current = layout
        while current.children:
            current = current.children[0]
        # 5 levels of padding=5 (each side), so 5*5*2 = 50 total
        assert current.width <= 300 - 50

    def test_max_width_zero(self):
        box = Box(style=Style(width=100, height=50, max_width=0))
        layout = compute_layout(box, 300, 300)
        assert layout.width == 0

    def test_max_and_min_both_set_min_wins(self):
        box = Box(style=Style(width=80, height=50, max_width=30, min_width=50))
        layout = compute_layout(box, 300, 300)
        assert layout.width == 50


# ---------------------------------------------------------------------------
# Category 10: Backward Compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_existing_explicit_width_text_unchanged(self):
        text = Text("Hello", style=Style(width=150, font_size=12))
        layout = compute_layout(text, 500, 500)
        assert layout.width == 150

    def test_existing_explicit_height_text_unchanged(self):
        text = Text("Hello", style=Style(height=40, font_size=12))
        layout = compute_layout(text, 500, 500)
        assert layout.height == 40

    def test_existing_flex_grow_text_starts_at_zero(self):
        text = Text("Hello", style=Style(flex_grow=1, font_size=12))
        root = Box(
            style=Style(width=200, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 200, 50)
        text_l = layout.children[0]
        # flex_grow=1 should give it the full 200px
        assert text_l.width == 200


# ---------------------------------------------------------------------------
# Category 11: font_shrink
# ---------------------------------------------------------------------------

class TestFontShrink:
    def test_font_shrink_reduces_layout_width(self):
        """Text with font_shrink=True in a narrow container fits within container."""
        text = Text(
            "Very long species name here that should be truncated",
            style=Style(font_size=20, font_shrink=True),
        )
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 100, 50)
        text_l = layout.children[0]
        assert text_l.width <= 100

    def test_font_shrink_stores_resolved_size(self):
        """LayoutBox.resolved_font_size is set smaller than original font_size."""
        text = Text(
            "Very long species name here that should be truncated",
            style=Style(font_size=20, font_shrink=True),
        )
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 100, 50)
        text_l = layout.children[0]
        assert text_l.resolved_font_size is not None
        assert text_l.resolved_font_size < 20

    def test_font_shrink_no_change_when_fits(self):
        """Short text with font_shrink=True keeps resolved_font_size=None."""
        text = Text("Hi", style=Style(font_size=12, font_shrink=True))
        root = Box(
            style=Style(width=500, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 500, 50)
        text_l = layout.children[0]
        assert text_l.resolved_font_size is None

    def test_font_shrink_false_clips_instead(self):
        """Without font_shrink, text is capped but resolved_font_size is None."""
        text = Text(
            "Very long species name here that should be truncated",
            style=Style(font_size=20),
        )
        root = Box(
            style=Style(width=100, height=50, flex_direction="row"),
            children=[text],
        )
        layout = compute_layout(root, 100, 50)
        text_l = layout.children[0]
        assert text_l.resolved_font_size is None
        assert text_l.width <= 100

    def test_font_shrink_renders_full_text(self):
        """Rendered image with font_shrink=True has non-background pixels near the right edge."""
        text = Text(
            "Red-bellied Woodpecker Extra Long Name",
            style=Style(font_size=30, font_color=(0, 0, 0), font_shrink=True),
        )
        container_w = 150
        root = Box(
            style=Style(width=container_w, height=50, background=(255, 255, 255),
                        flex_direction="row"),
            children=[text],
        )
        img = render(root, container_w, 50, background=(255, 255, 255))
        # Check that there are non-white pixels in the right third of the container
        has_text_right = False
        for x in range(container_w * 2 // 3, container_w):
            for y in range(50):
                if img.getpixel((x, y)) != (255, 255, 255):
                    has_text_right = True
                    break
            if has_text_right:
                break
        assert has_text_right, "font_shrink text should be visible near the right edge"
