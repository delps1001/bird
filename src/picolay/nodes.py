from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from PIL import Image

from .style import Style


@dataclass
class Box:
    style: Style = field(default_factory=Style)
    children: list[Union[Box, Text, Img]] = field(default_factory=list)


@dataclass
class Text:
    content: str = ""
    style: Style = field(default_factory=Style)

    def __init__(self, content: str = "", *, style: Optional[Style] = None):
        self.content = content
        self.style = style or Style()


@dataclass
class Img:
    src: Union[Image.Image, Path, str, None] = None
    style: Style = field(default_factory=Style)

    def __init__(
        self,
        src: Union[Image.Image, Path, str, None] = None,
        *,
        style: Optional[Style] = None,
    ):
        self.src = src
        self.style = style or Style()

    def load_image(self) -> Optional[Image.Image]:
        if self.src is None:
            return None
        if isinstance(self.src, Image.Image):
            return self.src
        return Image.open(self.src).convert("RGBA")
