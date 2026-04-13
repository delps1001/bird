from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


def _normalize_sides(value) -> tuple[int, int, int, int]:
    """Convert padding/margin shorthand to (top, right, bottom, left)."""
    if value is None:
        return (0, 0, 0, 0)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        v = int(value)
        return (v, v, v, v)
    if isinstance(value, tuple):
        if len(value) == 2:
            tb, lr = int(value[0]), int(value[1])
            return (tb, lr, tb, lr)
        if len(value) == 4:
            return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
    raise ValueError(f"Invalid sides value: {value!r}. Use int, (tb, lr), or (t, r, b, l).")


def _normalize_border(value) -> tuple[int, tuple[int, int, int]]:
    """Convert border spec to (width, (r, g, b))."""
    if value is None:
        return (0, (0, 0, 0))
    if isinstance(value, tuple) and len(value) == 2:
        return (int(value[0]), tuple(value[1]))
    raise ValueError(f"Invalid border value: {value!r}. Use (width, (r, g, b)).")


@dataclass(frozen=True)
class Style:
    width: Optional[float] = None
    height: Optional[float] = None
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    max_width: Optional[float] = None
    max_height: Optional[float] = None

    padding: tuple[int, int, int, int] = (0, 0, 0, 0)
    margin: tuple[int, int, int, int] = (0, 0, 0, 0)
    border: tuple[int, tuple[int, int, int]] = (0, (0, 0, 0))

    background: Optional[tuple[int, int, int]] = None

    flex_direction: str = "row"
    justify_content: str = "start"
    align_items: str = "start"
    gap: int = 0
    flex_grow: float = 0.0

    object_fit: str = "contain"
    image_rendering: str = "auto"  # "auto" (LANCZOS) or "pixelated" (NEAREST)

    font_size: int = 16
    font_color: tuple[int, int, int] = (0, 0, 0)
    text_align: str = "left"
    font_shrink: bool = False

    overflow: str = "visible"

    def __init__(self, **kwargs):
        # Normalize padding, margin, border before freezing
        pad = _normalize_sides(kwargs.pop("padding", None))
        mar = _normalize_sides(kwargs.pop("margin", None))
        bor = _normalize_border(kwargs.pop("border", None))

        object.__setattr__(self, "padding", pad)
        object.__setattr__(self, "margin", mar)
        object.__setattr__(self, "border", bor)

        # Set remaining fields from kwargs or defaults
        for f in self.__dataclass_fields__:
            if f in ("padding", "margin", "border"):
                continue
            if f in kwargs:
                object.__setattr__(self, f, kwargs.pop(f))
            else:
                object.__setattr__(self, f, self.__dataclass_fields__[f].default)

        if kwargs:
            raise TypeError(f"Unexpected keyword arguments: {set(kwargs)}")

    @property
    def padding_top(self) -> int:
        return self.padding[0]

    @property
    def padding_right(self) -> int:
        return self.padding[1]

    @property
    def padding_bottom(self) -> int:
        return self.padding[2]

    @property
    def padding_left(self) -> int:
        return self.padding[3]

    @property
    def margin_top(self) -> int:
        return self.margin[0]

    @property
    def margin_right(self) -> int:
        return self.margin[1]

    @property
    def margin_bottom(self) -> int:
        return self.margin[2]

    @property
    def margin_left(self) -> int:
        return self.margin[3]

    @property
    def border_width(self) -> int:
        return self.border[0]

    @property
    def border_color(self) -> tuple[int, int, int]:
        return self.border[1]

    @property
    def h_padding(self) -> int:
        return self.padding_left + self.padding_right

    @property
    def v_padding(self) -> int:
        return self.padding_top + self.padding_bottom

    @property
    def h_margin(self) -> int:
        return self.margin_left + self.margin_right

    @property
    def v_margin(self) -> int:
        return self.margin_top + self.margin_bottom

    @property
    def h_border(self) -> int:
        return self.border_width * 2

    @property
    def v_border(self) -> int:
        return self.border_width * 2
