from __future__ import annotations

from pathlib import Path

from PIL import Image


class FileDisplayDriver:
    """Saves rendered images to disk as PNG files."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def show(self, image: Image.Image) -> None:
        path = self._output_dir / "display.png"
        image.save(path)
