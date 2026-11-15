"""Focus renderer: a single bird, vertically stacked and centered.

Shows only the top-ranked bird (new species first, otherwise the rarest in
the recent window): large pixel-art image, then common name, scientific
name, and a count line. Newly-recognized species show a star in place of the count.
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
_BG = (255, 255, 255)
_DARK = (40, 40, 40)
_MUTED = (130, 130, 130)
_ACCENT = (235, 87, 87)


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
    return f"Last seen {seen.strftime('%b')} {_ordinal(seen.day)} {clock}"


_QR_MODULE_PX = 3
_QR_QUIET_MODULES = 2


def qr_image(url: str) -> Image.Image:
    """Smallest practical QR code for ``url``: low error correction, 3px modules."""
    import segno  # lazy: only needed when a QR code is requested

    matrix = segno.make(url, error="l", micro=False).matrix
    n = len(matrix)
    quiet = _QR_QUIET_MODULES
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
                        font_size=max(_MIN_FONT, height // 16), font_color=_MUTED)),
                ],
            )
            return render(tree, width, height, background=_BG)

        bird = birds[0]
        art = load_bird_image(bird.common_name, assets_dir)
        bbox = art.getchannel("A").getbbox()  # trim transparent padding so the bird fills its area
        if bbox:
            art = art.crop(bbox)
        img_h = round(usable_h * 0.66)
        text_h = usable_h - img_h
        name_sz = max(_MIN_FONT, min(text_h // 4, usable_w // 10))
        sci_sz = max(_MIN_FONT, name_sz * 2 // 3)
        stat_sz = max(_MIN_FONT, name_sz * 2 // 3)

        # Same convention as the other renderers: a star replaces the count for new species.
        stats = "\u2605" if bird.is_new else f"{bird.lifetime_count}x"
        stat_color = _ACCENT if bird.is_new else _MUTED
        if bird.is_new:
            stat_sz = name_sz

        last_seen = (
            format_last_seen(bird.last_detected_at, self._now())
            if bird.last_detected_at else None
        )
        seen_sz = max(_MIN_FONT, name_sz // 2)

        root = Box(
            style=Style(
                width=width, height=height, background=_BG, padding=padding,
                flex_direction="column", align_items="center",
            ),
            children=[
                Img(
                    src=art,
                    style=Style(
                        width=usable_w, height=img_h,
                        object_fit="contain", image_rendering="pixelated",
                    ),
                ),
                Box(
                    style=Style(
                        width=usable_w, height=text_h, flex_direction="column",
                        align_items="center", justify_content="center",
                        overflow="hidden", gap=max(2, name_sz // 5),
                    ),
                    children=[
                        Text(bird.common_name, style=Style(
                            font_size=name_sz, font_color=_DARK,
                            text_align="center", font_shrink=True)),
                        Text(bird.scientific_name, style=Style(
                            font_size=sci_sz, font_color=_MUTED,
                            text_align="center", font_shrink=True)),
                        Text(stats, style=Style(
                            font_size=stat_sz, font_color=stat_color,
                            text_align="center", font_shrink=True)),
                        *(
                            [Text(last_seen, style=Style(
                                font_size=seen_sz, font_color=_MUTED,
                                text_align="center", font_shrink=True))]
                            if last_seen else []
                        ),
                    ],
                ),
            ],
        )
        image = render(root, width, height, background=_BG)
        if self._qr_base_url and bird.last_detection_id is not None:
            url = f"{self._qr_base_url}/ui/detections/{bird.last_detection_id}"
            qr = qr_image(url)
            # Bottom-right corner, inside the frame inset.
            x = width - padding[1] - qr.width
            y = height - padding[2] - qr.height
            image.paste(qr, (x, y))
        return image
