"""Tiny HTTP redirect so a static NFC tag can open the bird currently on screen.

The tag holds a fixed URL (``http://<frame>:<port>/latest``). Each time the
display renders, :class:`RecordingRenderer` notes the detection id of the bird
shown; ``GET /latest`` answers with a 302 to that detection's BirdNET-Go page,
the same link the focus renderer's QR code encodes.

The renderer is wrapped, not modified, so this works with any renderer.
"""
from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image

from bird_listener.persistence.models import BirdSummary
from bird_listener.ports import DisplayRenderer

logger = logging.getLogger(__name__)


class CurrentDetection:
    """Thread-safe holder for the detection id currently on the display."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._id: int | None = None

    def set(self, detection_id: int | None) -> None:
        with self._lock:
            self._id = detection_id

    def get(self) -> int | None:
        with self._lock:
            return self._id


class RecordingRenderer:
    """Delegates to ``inner`` and records the detection id of the top bird."""

    def __init__(self, inner: DisplayRenderer, current: CurrentDetection) -> None:
        self._inner = inner
        self._current = current

    def __getattr__(self, name: str):
        # max_birds, shows_last_seen, etc. are read by the orchestrator.
        return getattr(self._inner, name)

    def render(
        self,
        birds: list[BirdSummary],
        assets_dir: Path,
        width: int,
        height: int,
    ) -> Image.Image:
        image = self._inner.render(birds, assets_dir, width, height)
        self._current.set(birds[0].last_detection_id if birds else None)
        return image


def detection_url(base_url: str, detection_id: int) -> str:
    return f"{base_url.rstrip('/')}/ui/detections/{detection_id}"


def make_server(
    base_url: str,
    current: CurrentDetection,
    port: int,
    host: str = "0.0.0.0",
) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0].rstrip("/")
            if path == "/latest":
                detection_id = current.get()
                if detection_id is None:
                    self._reply(503, "No detection on display yet.\n")
                    return
                self.send_response(302)
                self.send_header("Location", detection_url(base_url, detection_id))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", "0")
                self.end_headers()
            elif path == "/healthz":
                self._reply(200, "ok\n")
            else:
                self._reply(404, "Not found. Try /latest\n")

        def _reply(self, code: int, body: str) -> None:
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            logger.info("nfc-redirect: " + format, *args)

    return ThreadingHTTPServer((host, port), Handler)


def start_server(base_url: str, current: CurrentDetection, port: int) -> ThreadingHTTPServer:
    """Start the redirect server on a daemon thread and return it."""
    server = make_server(base_url, current, port)
    threading.Thread(target=server.serve_forever, daemon=True, name="nfc-redirect").start()
    logger.info("NFC redirect listening on :%d (/latest -> %s/ui/detections/<id>)", port, base_url.rstrip("/"))
    return server
