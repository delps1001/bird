from __future__ import annotations

from pathlib import Path

from bird_listener.display.focus_renderer import FocusRenderer
from bird_listener.persistence.models import BirdSummary

ASSETS_DIR = Path(__file__).parent.parent / "assets" / "birds"


def _bird(name: str, count: int, *, is_new: bool = False) -> BirdSummary:
    return BirdSummary(
        common_name=name, scientific_name="x y", lifetime_count=count,
        recent_count=2, best_confidence=0.9, is_new=is_new,
    )


def test_max_birds_is_one() -> None:
    assert FocusRenderer().max_birds == 1


def test_renders_requested_size() -> None:
    img = FocusRenderer(inset=0.07).render([_bird("Bald Eagle", 1)], ASSETS_DIR, 480, 800)
    assert img.size == (480, 800)


def test_only_first_bird_is_shown() -> None:
    r = FocusRenderer()
    one = r.render([_bird("Bald Eagle", 1)], ASSETS_DIR, 800, 480)
    many = r.render([_bird("Bald Eagle", 1), _bird("Blue Jay", 9)], ASSETS_DIR, 800, 480)
    assert list(one.getdata()) == list(many.getdata())


def test_new_bird_differs_and_empty_renders() -> None:
    r = FocusRenderer()
    a = r.render([_bird("Bald Eagle", 1, is_new=True)], ASSETS_DIR, 800, 480)
    b = r.render([_bird("Bald Eagle", 1)], ASSETS_DIR, 800, 480)
    assert list(a.getdata()) != list(b.getdata())
    assert r.render([], ASSETS_DIR, 800, 480).size == (800, 480)


def test_format_last_seen() -> None:
    from datetime import datetime

    from bird_listener.display.focus_renderer import format_last_seen

    now = datetime(2026, 11, 15, 9, 5)
    assert format_last_seen(datetime(2026, 11, 15, 7, 8), now) == "Last seen Nov 15th 7:08 AM"
    assert format_last_seen(datetime(2026, 11, 14, 15, 42), now) == "Last seen Nov 14th 3:42 PM"
    assert format_last_seen(datetime(2026, 11, 1, 9, 0), now) == "Last seen Nov 1st 9:00 AM"
    assert format_last_seen(datetime(2026, 11, 22, 9, 0), now) == "Last seen Nov 22nd 9:00 AM"
    assert format_last_seen(datetime(2026, 11, 23, 9, 0), now) == "Last seen Nov 23rd 9:00 AM"
    assert format_last_seen(datetime(2026, 11, 11, 9, 0), now) == "Last seen Nov 11th 9:00 AM"
    assert format_last_seen(datetime(2026, 11, 12, 0, 1), now) == "Last seen Nov 12th 12:01 AM"


def test_last_seen_changes_render() -> None:
    from datetime import datetime

    now = datetime(2026, 11, 15, 12, 0)
    r = FocusRenderer(now=lambda: now)
    def with_seen(t):
        b = _bird("Barn Owl", 2)
        return BirdSummary(**{**b.__dict__, "last_detected_at": t})
    a = r.render([with_seen(datetime(2026, 11, 15, 9, 1))], ASSETS_DIR, 800, 480)
    b = r.render([with_seen(datetime(2026, 11, 15, 11, 30))], ASSETS_DIR, 800, 480)
    assert list(a.getdata()) != list(b.getdata())


def test_qr_code_only_with_base_url_and_detection_id() -> None:
    from dataclasses import replace

    b = replace(_bird("Barn Owl", 2), last_detection_id=142880)
    plain = FocusRenderer().render([b], ASSETS_DIR, 480, 800)
    with_qr = FocusRenderer(qr_base_url="http://192.168.1.91:8080").render([b], ASSETS_DIR, 480, 800)
    assert list(plain.getdata()) != list(with_qr.getdata())
    # No detection id -> no QR even when a base URL is configured.
    no_id = FocusRenderer(qr_base_url="http://192.168.1.91:8080").render(
        [_bird("Barn Owl", 2)], ASSETS_DIR, 480, 800)
    assert list(no_id.getdata()) == list(plain.getdata())


def test_qr_image_is_small_and_square() -> None:
    from bird_listener.display.focus_renderer import qr_image

    img = qr_image("http://192.168.1.91:8080/ui/detections/142880")
    assert img.width == img.height <= 100


def test_format_heard() -> None:
    from bird_listener.display.focus_renderer import format_heard

    assert format_heard(1) == "Once"
    assert format_heard(2) == "Twice"
    assert format_heard(14) == "14 times"
    assert format_heard(1234) == "1,234 times"


def test_qr_image_quiet_zone_is_optional() -> None:
    from bird_listener.display.focus_renderer import qr_image

    url = "http://192.168.1.91:8080/ui/detections/142880"
    # Default keeps a 2-module (6px) quiet zone on every side; quiet=0 drops it.
    assert qr_image(url).width - qr_image(url, quiet=0).width == 12
    assert qr_image(url, quiet=0).getpixel((0, 0)) == (0, 0, 0)  # finder pattern corner


def test_long_name_and_qr_stay_inside_the_inset() -> None:
    from dataclasses import replace
    from datetime import datetime

    b = replace(
        _bird("Black-and-white Warbler", 1234),
        last_detected_at=datetime(2026, 11, 14, 14, 50), last_detection_id=142880,
    )
    w, h, inset = 480, 800, 0.07
    img = FocusRenderer(inset=inset, qr_base_url="http://192.168.1.91:8080").render(
        [b], ASSETS_DIR, w, h)
    ix, iy = round(inset * w), round(inset * h)
    inner = (ix, iy, w - ix, h - iy)
    blank = img.copy()
    blank.paste((255, 255, 255), inner)
    assert blank.getextrema() == ((255, 255), (255, 255), (255, 255))


def test_text_uses_only_panel_palette_colours() -> None:
    """Below the sprite, only pure black/white/red (plus anti-aliasing) is drawn."""
    from datetime import datetime

    b = BirdSummary(
        common_name="Barn Owl", scientific_name="Tyto alba", lifetime_count=1,
        recent_count=1, best_confidence=0.9, is_new=True,
        last_detected_at=datetime(2026, 11, 14, 14, 50), last_detection_id=1,
    )
    img = FocusRenderer(qr_base_url="http://192.168.1.91:8080").render([b], ASSETS_DIR, 480, 800)
    colours = {c for _, c in img.crop((0, 700, 480, 800)).getcolors(maxcolors=100000)}
    assert (0, 0, 0) in colours and (255, 0, 0) in colours
    assert all(r >= g == b for r, g, b in colours)  # greys and reds only
