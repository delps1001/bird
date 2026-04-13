"""Integration tests: full bird-card-style layouts."""
import os
import pytest
from pathlib import Path
from PIL import Image
from picolay import Box, Text, Img, Style, render


OUTPUT_DIR = Path(__file__).parent / "output" / "picolay"


@pytest.fixture(autouse=True)
def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _solid_image(w, h, color=(100, 150, 200, 255)):
    return Image.new("RGBA", (w, h), color)


def _save(img, name):
    img.save(OUTPUT_DIR / f"{name}.png")


class TestIntegration:
    def test_hero_card_layout(self):
        card = Box(
            style=Style(width=200, height=300, flex_direction="column", background=(255, 255, 255)),
            children=[
                Img(src=_solid_image(200, 200), style=Style(flex_grow=0.7, object_fit="cover")),
                Box(
                    style=Style(flex_grow=0.3, flex_direction="column", align_items="center", justify_content="center"),
                    children=[Text("House Finch", style=Style(font_size=14, text_align="center"))],
                ),
            ],
        )
        img = render(card, 200, 300)
        _save(img, "hero_card")
        # Image region top 70%, text bottom 30%
        layout = __import__("picolay").compute_layout(card, 200, 300)
        img_h = layout.children[0].height
        text_h = layout.children[1].height
        assert img_h > text_h

    def test_secondary_card_layout(self):
        card = Box(
            style=Style(width=150, height=200, flex_direction="column", background=(240, 240, 240)),
            children=[
                Img(src=_solid_image(150, 150), style=Style(flex_grow=0.6, object_fit="contain")),
                Box(
                    style=Style(flex_grow=0.4, flex_direction="column", align_items="center"),
                    children=[Text("Sparrow", style=Style(font_size=12))],
                ),
            ],
        )
        img = render(card, 150, 200)
        _save(img, "secondary_card")
        layout = __import__("picolay").compute_layout(card, 150, 200)
        assert layout.children[0].height > layout.children[1].height

    def test_pillow_renderer_equivalent(self):
        """Hero top 65%, 2-column secondary bottom 35%."""
        hero = Box(
            style=Style(flex_grow=0.65, background=(150, 200, 150)),
            children=[
                Img(src=_solid_image(400, 200), style=Style(flex_grow=1, object_fit="cover")),
            ],
        )
        secondary = Box(
            style=Style(flex_grow=0.35, flex_direction="row"),
            children=[
                Box(
                    style=Style(flex_grow=1, flex_direction="column", background=(200, 150, 150)),
                    children=[Img(src=_solid_image(200, 150), style=Style(flex_grow=1, object_fit="cover"))],
                ),
                Box(
                    style=Style(flex_grow=1, flex_direction="column", background=(150, 150, 200)),
                    children=[Img(src=_solid_image(200, 150), style=Style(flex_grow=1, object_fit="cover"))],
                ),
            ],
        )
        root = Box(
            style=Style(width=400, height=300, flex_direction="column"),
            children=[hero, secondary],
        )
        img = render(root, 400, 300)
        _save(img, "pillow_renderer")
        layout = __import__("picolay").compute_layout(root, 400, 300)
        assert layout.children[0].height > layout.children[1].height
        # Two secondary columns side by side
        sec = layout.children[1]
        assert len(sec.children) == 2
        assert abs(sec.children[0].width - sec.children[1].width) <= 1

    def test_grid_renderer_equivalent(self):
        """Hero center + 2 side columns + 3 bottom columns + footer."""
        top_row = Box(
            style=Style(flex_grow=0.6, flex_direction="row"),
            children=[
                Box(style=Style(flex_grow=1, background=(200, 200, 200))),  # left side
                Box(style=Style(flex_grow=2, background=(150, 200, 150))),  # hero
                Box(style=Style(flex_grow=1, background=(200, 200, 200))),  # right side
            ],
        )
        bottom_row = Box(
            style=Style(flex_grow=0.3, flex_direction="row"),
            children=[
                Box(style=Style(flex_grow=1, background=(180, 180, 220))),
                Box(style=Style(flex_grow=1, background=(180, 220, 180))),
                Box(style=Style(flex_grow=1, background=(220, 180, 180))),
            ],
        )
        footer = Box(style=Style(flex_grow=0.1, background=(100, 100, 100)))
        root = Box(
            style=Style(width=800, height=480, flex_direction="column"),
            children=[top_row, bottom_row, footer],
        )
        img = render(root, 800, 480)
        _save(img, "grid_renderer")
        layout = __import__("picolay").compute_layout(root, 800, 480)
        # 3 sections
        assert len(layout.children) == 3
        # Hero is larger than side cells
        hero = layout.children[0].children[1]
        side = layout.children[0].children[0]
        assert hero.width > side.width

    def test_footer_bar_layout(self):
        footer = Box(
            style=Style(
                width=400,
                height=40,
                flex_direction="row",
                align_items="center",
                justify_content="center",
                gap=10,
                background=(50, 50, 50),
            ),
            children=[
                Img(src=_solid_image(24, 24), style=Style(width=24, height=24)),
                Text("BirdListener v1.0", style=Style(font_size=12, font_color=(255, 255, 255))),
            ],
        )
        img = render(footer, 400, 40)
        _save(img, "footer_bar")
        assert img.size == (400, 40)

    def test_render_to_exact_resolution_800x480(self):
        root = Box(
            style=Style(width=800, height=480, flex_direction="column", background=(255, 255, 255)),
            children=[
                Box(style=Style(flex_grow=0.65, background=(200, 220, 200))),
                Box(style=Style(flex_grow=0.35, flex_direction="row"), children=[
                    Box(style=Style(flex_grow=1, background=(220, 200, 200))),
                    Box(style=Style(flex_grow=1, background=(200, 200, 220))),
                    Box(style=Style(flex_grow=1, background=(220, 220, 200))),
                ]),
            ],
        )
        img = render(root, 800, 480)
        assert img.size == (800, 480)
        _save(img, "800x480")

    def test_render_to_exact_resolution_400x300(self):
        root = Box(
            style=Style(width=400, height=300, flex_direction="column", background=(255, 255, 255)),
            children=[Box(style=Style(flex_grow=1, background=(200, 200, 200)))],
        )
        img = render(root, 400, 300)
        assert img.size == (400, 300)

    def test_render_to_exact_resolution_1200x825(self):
        root = Box(
            style=Style(width=1200, height=825, flex_direction="column", background=(255, 255, 255)),
            children=[Box(style=Style(flex_grow=1, background=(200, 200, 200)))],
        )
        img = render(root, 1200, 825)
        assert img.size == (1200, 825)

    def test_inset_equivalent(self):
        """Outer padding matching 2% inset."""
        root = Box(
            style=Style(
                width=800,
                height=480,
                padding=(10, 16, 10, 16),  # ~2% of dimensions
                background=(255, 255, 255),
            ),
            children=[Box(style=Style(flex_grow=1, background=(200, 200, 200)))],
        )
        img = render(root, 800, 480)
        _save(img, "inset")
        # Corners should be white (inset)
        assert img.getpixel((5, 5)) == (255, 255, 255)
        # Center should be gray
        assert img.getpixel((400, 240)) == (200, 200, 200)

    def test_card_with_image_and_two_text_lines(self):
        card = Box(
            style=Style(
                width=200,
                height=300,
                flex_direction="column",
                align_items="center",
                background=(255, 255, 255),
            ),
            children=[
                Img(src=_solid_image(180, 180), style=Style(flex_grow=1, object_fit="contain")),
                Text("House Finch", style=Style(font_size=18, font_color=(0, 0, 0), text_align="center")),
                Text("5x lifetime", style=Style(font_size=12, font_color=(80, 80, 80), text_align="center")),
            ],
        )
        img = render(card, 200, 300)
        _save(img, "card_two_lines")
        layout = __import__("picolay").compute_layout(card, 200, 300)
        # Three children stacked
        assert len(layout.children) == 3
        # Image at top, text nodes below
        assert layout.children[0].y < layout.children[1].y < layout.children[2].y

    def test_six_bird_grid_all_cells_non_empty(self):
        colors = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
            (255, 255, 100), (255, 100, 255), (100, 255, 255),
        ]
        cells = [
            Img(src=_solid_image(100, 100, c + (255,)), style=Style(flex_grow=1, object_fit="cover"))
            for c in colors
        ]
        top_row = Box(
            style=Style(flex_grow=0.6, flex_direction="row"),
            children=[
                Box(style=Style(flex_grow=1), children=[cells[0]]),
                Box(style=Style(flex_grow=2), children=[cells[1]]),
                Box(style=Style(flex_grow=1), children=[cells[2]]),
            ],
        )
        bottom_row = Box(
            style=Style(flex_grow=0.4, flex_direction="row"),
            children=[
                Box(style=Style(flex_grow=1), children=[cells[3]]),
                Box(style=Style(flex_grow=1), children=[cells[4]]),
                Box(style=Style(flex_grow=1), children=[cells[5]]),
            ],
        )
        root = Box(
            style=Style(width=600, height=400, flex_direction="column"),
            children=[top_row, bottom_row],
        )
        img = render(root, 600, 400)
        _save(img, "six_bird_grid")
        # Each region should have non-white pixels
        regions = [
            (75, 60), (300, 60), (525, 60),  # top row
            (100, 300), (300, 300), (500, 300),  # bottom row
        ]
        for rx, ry in regions:
            p = img.getpixel((rx, ry))
            assert p != (255, 255, 255), f"Region ({rx},{ry}) is white"

    def test_layout_as_pure_function(self):
        card = Box(
            style=Style(width=100, height=100, flex_direction="column", background=(200, 200, 200)),
            children=[
                Box(style=Style(flex_grow=1, background=(255, 0, 0))),
                Box(style=Style(flex_grow=1, background=(0, 0, 255))),
            ],
        )
        img1 = render(card, 100, 100)
        img2 = render(card, 100, 100)
        assert img1.tobytes() == img2.tobytes()
