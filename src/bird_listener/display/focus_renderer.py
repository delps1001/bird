"""Focus renderer: a single bird, laid out like a museum label.

Shows only the top-ranked bird (new species first, otherwise the rarest in
the recent window): large pixel-art image, then a left-aligned caption block:
common name, scientific name, a thin rule, and two small label/value facts
(last seen, how often heard). Newly-recognized species show a star in the
accent colour in place of the count. When a QR base URL is configured, a small
QR code sits on the right of the facts, captioned "LISTEN".
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from PIL import Image

from bird_listener.display.common import load_bird_image
from bird_listener.persistence.models import BirdSummary
from picolay import Box, Img, Style, Text, render

_MIN_FONT = 6
# Pure panel-palette colours only: anything in between (greys, soft reds) is
# dithered into speckles on the 6-colour e-ink panel, which ruins thin text.
_BG = (255, 255, 255)
_INK = (0, 0, 0)
_ACCENT = (255, 0, 0)
_HAIR = "\u200a"  # hair space, used to letter-space the small-caps labels


def _ordinal(day: int) -> str:
    if 11 <= day % 100 <= 13:
        return f"{day}th"
    return f"{day}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th') }"


def format_last_seen(seen: datetime, now: datetime) -> str:
    """Always the explicit date and time, e.g. 'Last seen Nov 9th 3:42 PM'.

    The date is shown even for today so a frozen display is obvious at a glance.
    The ``now`` argument is kept for API compatibility. Datetimes are naive local time.
    """
    clock = seen.strftime("%I:%M %p").lstrip("0")
    return f"Last seen {_date_part(seen)} {clock}"


def _date_part(seen: datetime) -> str:
    return f"{seen.strftime('%b')} {_ordinal(seen.day)}"


def _clock_part(seen: datetime) -> str:
    return seen.strftime("%I:%M %p").lstrip("0")


def format_heard(count: int) -> str:
    """Lifetime detection count in words: 'Once', 'Twice', '14 times'."""
    if count <= 1:
        return "Once"
    if count == 2:
        return "Twice"
    return f"{count:,} times"


def _caps(text: str) -> str:
    """Upper-case and letter-space a short label (hair spaces between letters)."""
    return "  ".join(_HAIR.join(word) for word in text.upper().split())


_QR_MODULE_PX = 3
_QR_QUIET_MODULES = 2


def qr_image(url: str, quiet: int = _QR_QUIET_MODULES) -> Image.Image:
    """Smallest practical QR code for ``url``: low error correction, 3px modules.

    ``quiet`` is the white border in modules. Pass 0 only when the surrounding
    layout guarantees at least that much white space on every side.
    """
    import segno  # lazy: only needed when a QR code is requested

    matrix = segno.make(url, error="l", micro=False).matrix
    n = len(matrix)
    size = (n + 2 * quiet) * _QR_MODULE_PX
    img = Image.new("RGB", (size, size), (255, 255, 255))
    px = img.load()
    for r, row in enumerate(matrix):
        for c, v in enumerate(row):
            if v:
                for dy in range(_QR_MODULE_PX):
                    for dx in range(_QR_MODULE_PX):
                        px[(c + quiet) * _QR_MODULE_PX + dx, (r + quiet) * _QR_MODULE_PX + dy] = (0, 0, 0)
    return img


class FocusRenderer:
    """Single-bird vertical layout showing only the rarest recent bird."""

    # Orchestrator re-renders when a displayed bird's last-detected time changes.
    shows_last_seen = True

    def __init__(
        self,
        inset: float = 0.0,
        now: Callable[[], datetime] = datetime.now,
        qr_base_url: str | None = None,
    ):
        self._inset = inset
        self._now = now
        # e.g. "http://192.168.1.91:8080": when set, a tiny QR code links to the
        # BirdNET-Go page (with audio) for the displayed bird's latest detection.
        self._qr_base_url = qr_base_url.rstrip("/") if qr_base_url else None

    @property
    def max_birds(self) -> int:
        return 1

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        inset_x = round(self._inset * width)
        inset_y = round(self._inset * height)
        pad = max(4, min(width, height) // 50)
        padding = (pad + inset_y, pad + inset_x, pad + inset_y, pad + inset_x)
        usable_w = width - padding[1] - padding[3]
        usable_h = height - padding[0] - padding[2]

        if not birds:
            tree = Box(
                style=Style(
                    width=width, height=height, background=_BG, padding=padding,
                    flex_direction="column", align_items="center",
                    justify_content="center",
                ),
                children=[
                    Text("Listening...", style=Style(
                        font_size=max(_MIN_FONT, height // 16), font_color=_INK)),
                ],
            )
            return render(tree, width, height, background=_BG)

        bird = birds[0]
        art = load_bird_image(bird.common_name, assets_dir)
        bbox = art.getchannel("A").getbbox()  # trim transparent padding so the bird fills its area
        if bbox:
            art = art.crop(bbox)
        qr = None
        if self._qr_base_url and bird.last_detection_id is not None:
            # No built-in quiet zone, so the modules sit flush with the right margin
            # and the rule above; the layout keeps >= 2 modules of white around it.
            qr = qr_image(f"{self._qr_base_url}/ui/detections/{bird.last_detection_id}", quiet=0)

        # Type scale, all derived from the name size.
        unit = min(usable_w, usable_h)
        name_sz = max(_MIN_FONT, unit // 10)
        sci_sz = max(_MIN_FONT, round(name_sz * 0.56))
        value_sz = sci_sz
        label_sz = max(_MIN_FONT, round(name_sz * 0.36))
        rule_px = max(1, name_sz // 20)
        space = max(2, round(name_sz * 0.36))  # the one spacing step used throughout

        def line_h(size: int) -> int:
            return round(size * 1.25)

        def text(content, size, color=_INK, *, align="left", w=None, margin=0):
            return Text(content, style=Style(
                width=w, height=line_h(size), font_size=size, font_color=color,
                text_align=align, font_shrink=True, margin=margin))

        def fact(label, value, color=_INK, w=None):
            """A small-caps label over its value."""
            return Box(
                style=Style(
                    width=w, height=line_h(label_sz) + line_h(value_sz),
                    flex_direction="column", align_items="start",
                ),
                children=[text(_caps(label), label_sz, w=w), text(value, value_sz, color, w=w)],
            )

        fact_h = line_h(label_sz) + line_h(value_sz)
        qr_col_w = qr.width if qr else 0
        col_gap = 2 * space if qr else 0
        facts_w = usable_w - qr_col_w - col_gap

        # Same convention as the other renderers: a star replaces the count for new species.
        if bird.is_new:
            heard = ("Life list", "\u2605 New species", _ACCENT)
        else:
            heard = ("Heard", format_heard(bird.lifetime_count), _INK)
        seen = bird.last_detected_at
        facts = []
        if seen:
            facts.append(("Last seen", f"{_date_part(seen)} \u00b7 {_clock_part(seen)}", _INK))
        facts.append(heard)

        if qr:
            # Facts stacked on the left, spanning the height of the QR + its caption.
            footer_h = max(qr.height + space // 2 + line_h(label_sz),
                           len(facts) * fact_h + space)
            footer = Box(
                style=Style(width=usable_w, height=footer_h, flex_direction="row", gap=col_gap),
                children=[
                    Box(
                        style=Style(
                            width=facts_w, height=footer_h, flex_direction="column",
                            justify_content="space_between" if len(facts) > 1 else "start",
                        ),
                        children=[fact(lb, v, c, w=facts_w) for lb, v, c in facts],
                    ),
                    Box(
                        style=Style(
                            width=qr_col_w, height=footer_h, flex_direction="column",
                            align_items="center", justify_content="space_between",
                        ),
                        children=[
                            Img(src=qr, style=Style(
                                width=qr.width, height=qr.height,
                                object_fit="contain", image_rendering="pixelated")),
                            text("\u25b6 " + _caps("Listen"), label_sz, align="center", w=qr_col_w),
                        ],
                    ),
                ],
            )
        else:
            # No QR: the facts sit side by side, the wider (date) column first.
            footer_h = fact_h
            first_w = round((usable_w - 2 * space) * 0.58)
            widths = [first_w, usable_w - 2 * space - first_w]
            footer = Box(
                style=Style(width=usable_w, height=footer_h, flex_direction="row", gap=2 * space),
                children=[fact(lb, v, c, w=w) for (lb, v, c), w in zip(facts, widths)],
            )

        caption = [
            text(bird.common_name, name_sz, w=usable_w, margin=(space, 0, 0, 0)),
            text(bird.scientific_name, sci_sz, w=usable_w),
            Box(style=Style(width=usable_w, height=rule_px, background=_INK,
                            margin=(space, 0, space, 0))),
            footer,
        ]
        text_h = (space + line_h(name_sz) + line_h(sci_sz)
                  + space + rule_px + space + footer_h)
        img_h = max(0, usable_h - text_h)

        root = Box(
            style=Style(
                width=width, height=height, background=_BG, padding=padding,
                flex_direction="column", align_items="start",
            ),
            children=[
                Img(
                    src=art,
                    style=Style(
                        width=usable_w, height=img_h,
                        object_fit="contain", image_rendering="pixelated",
                    ),
                ),
                *caption,
            ],
        )
        return render(root, width, height, background=_BG)
