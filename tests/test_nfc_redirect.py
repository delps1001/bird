from __future__ import annotations

import http.client
import threading
from pathlib import Path

from PIL import Image

from bird_listener.nfc_redirect import (
    CurrentDetection,
    RecordingRenderer,
    detection_url,
    make_server,
)
from bird_listener.persistence.models import BirdSummary


class StubRenderer:
    max_birds = 1
    shows_last_seen = True

    def render(self, birds, assets_dir: Path, width: int, height: int) -> Image.Image:
        return Image.new("RGB", (width, height), "white")


def _bird(det_id: int | None) -> BirdSummary:
    return BirdSummary(
        common_name="Carolina Wren",
        scientific_name="Thryothorus ludovicianus",
        lifetime_count=1,
        recent_count=1,
        best_confidence=0.9,
        last_detection_id=det_id,
    )


def _get(server, path: str):
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = resp.read()
    return resp, body


def _serve(current: CurrentDetection, base: str = "http://192.168.1.91:8080/"):
    server = make_server(base, current, port=0, host="127.0.0.1")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_detection_url_matches_qr_format():
    assert detection_url("http://h:8080/", 42) == "http://h:8080/ui/detections/42"


def test_recording_renderer_delegates_and_records_top_bird():
    current = CurrentDetection()
    r = RecordingRenderer(StubRenderer(), current)
    assert r.max_birds == 1 and r.shows_last_seen is True  # attribute passthrough
    img = r.render([_bird(7), _bird(9)], Path("."), 10, 10)
    assert img.size == (10, 10)
    assert current.get() == 7


def test_recording_renderer_clears_when_no_birds():
    current = CurrentDetection()
    current.set(5)
    RecordingRenderer(StubRenderer(), current).render([], Path("."), 4, 4)
    assert current.get() is None


def test_latest_redirects_to_current_detection():
    current = CurrentDetection()
    current.set(123)
    server = _serve(current)
    try:
        resp, _ = _get(server, "/latest")
        assert resp.status == 302
        assert resp.getheader("Location") == "http://192.168.1.91:8080/ui/detections/123"
        # Follows the display: a new render changes the target.
        current.set(124)
        resp, _ = _get(server, "/latest?from=nfc")
        assert resp.getheader("Location").endswith("/ui/detections/124")
    finally:
        server.shutdown()
        server.server_close()


def test_latest_503_before_first_render_and_404_elsewhere():
    server = _serve(CurrentDetection())
    try:
        assert _get(server, "/latest")[0].status == 503
        assert _get(server, "/nope")[0].status == 404
        resp, body = _get(server, "/healthz")
        assert resp.status == 200 and body == b"ok\n"
    finally:
        server.shutdown()
        server.server_close()
