from __future__ import annotations

from PIL import Image

from bird_listener.display.layout import (
    LayoutRegion,
    fit_image,
    resolve,
    scale_font_size,
)


def test_resolve_basic() -> None:
    region = LayoutRegion(x_frac=0.0, y_frac=0.0, w_frac=1.0, h_frac=0.65)
    x, y, w, h = resolve(region, 800, 480)
    assert (x, y) == (0, 0)
    assert w == 800
    assert h == 312  # round(0.65 * 480)


def test_resolve_secondary() -> None:
    region = LayoutRegion(x_frac=0.0, y_frac=0.65, w_frac=1.0, h_frac=0.35)
    x, y, w, h = resolve(region, 800, 480)
    assert x == 0
    assert y == 312
    assert w == 800
    assert h == 168


def test_resolve_scales_proportionally() -> None:
    region = LayoutRegion(x_frac=0.1, y_frac=0.2, w_frac=0.5, h_frac=0.3)
    # At 400x300
    x1, y1, w1, h1 = resolve(region, 400, 300)
    # At 800x600 (2x)
    x2, y2, w2, h2 = resolve(region, 800, 600)
    assert x2 == x1 * 2
    assert y2 == y1 * 2
    assert w2 == w1 * 2
    assert h2 == h1 * 2


def test_fit_image_landscape() -> None:
    img = Image.new("RGB", (100, 50))
    result = fit_image(img, 200, 200)
    assert result.width == 200
    assert result.height == 100


def test_fit_image_portrait() -> None:
    img = Image.new("RGB", (50, 100))
    result = fit_image(img, 200, 200)
    assert result.width == 100
    assert result.height == 200


def test_fit_image_preserves_aspect_ratio() -> None:
    img = Image.new("RGB", (32, 32))
    result = fit_image(img, 100, 50)
    assert result.width == 50
    assert result.height == 50


def test_scale_font_size_at_reference() -> None:
    assert scale_font_size(20, 480, 480) == 20


def test_scale_font_size_double() -> None:
    assert scale_font_size(20, 960, 480) == 40


def test_scale_font_size_half() -> None:
    assert scale_font_size(20, 240, 480) == 10
