from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from .fonts import load_font
from .nodes import Box, Img, Text
from .style import Style

Node = Union[Box, Text, Img]


@dataclass
class LayoutBox:
    """Resolved layout information for a node."""
    node: Node
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0
    children: list[LayoutBox] = None
    resolved_font_size: int | None = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


def _resolve_dimension(value, parent_size: float) -> float | None:
    """Resolve a width/height value. Fractions (0 < v <= 1.0) are relative to parent."""
    if value is None:
        return None
    if isinstance(value, float) and 0.0 < value <= 1.0:
        return value * parent_size
    return float(value)


def _text_intrinsic_size(node: Text, font_size: int | None = None) -> tuple[float, float]:
    """Compute intrinsic (width, height) of a text node."""
    if not node.content:
        return (0, 0)
    font = load_font(size=font_size or node.style.font_size)
    bbox = font.getbbox(node.content)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    return (w, h)


def _img_intrinsic_size(node: Img) -> tuple[float, float]:
    """Get intrinsic size of the source image."""
    img = node.load_image()
    if img is None:
        return (0, 0)
    return (float(img.width), float(img.height))


def compute_layout(node: Node, available_w: float, available_h: float) -> LayoutBox:
    """Compute layout for the full node tree, starting at (0, 0)."""
    return _layout_node(node, available_w, available_h, parent_is_row=True, has_flex_grow=False)


def _layout_node(
    node: Node,
    available_w: float,
    available_h: float,
    parent_is_row: bool = True,
    has_flex_grow: bool = False,
) -> LayoutBox:
    """Layout a single node within available space.

    has_flex_grow: if True and node has no explicit main-axis size, start at 0
    (space will be assigned during flex_grow distribution in the parent).
    """
    s = node.style

    w = _resolve_dimension(s.width, available_w)
    h = _resolve_dimension(s.height, available_h)

    if isinstance(node, Text):
        font_size = s.font_size
        iw, ih = _text_intrinsic_size(node, font_size)

        # Auto-shrink font to fit available width
        if s.font_shrink:
            if w is not None:
                max_content_w = w - s.h_padding - s.h_border
            else:
                max_content_w = available_w - s.h_padding - s.h_border
            while font_size > 1 and iw > max_content_w:
                font_size -= 1
                iw, ih = _text_intrinsic_size(node, font_size)

        if w is None:
            if has_flex_grow and s.flex_grow > 0 and parent_is_row:
                w = 0
            else:
                w = min(iw + s.h_padding + s.h_border, available_w)
        if h is None:
            if has_flex_grow and s.flex_grow > 0 and not parent_is_row:
                h = 0
            else:
                h = min(ih + s.v_padding + s.v_border, available_h)
        if s.max_width is not None:
            w = min(w, _resolve_dimension(s.max_width, available_w))
        if s.max_height is not None:
            h = min(h, _resolve_dimension(s.max_height, available_h))
        if s.min_width is not None:
            w = max(w, float(s.min_width))
        if s.min_height is not None:
            h = max(h, float(s.min_height))
        lb = LayoutBox(node=node, width=w, height=h)
        if font_size != s.font_size:
            lb.resolved_font_size = font_size
        return lb

    if isinstance(node, Img):
        iw, ih = _img_intrinsic_size(node)
        if w is None:
            if has_flex_grow and s.flex_grow > 0 and parent_is_row:
                w = 0
            else:
                w = min(iw + s.h_padding + s.h_border, available_w)
        if h is None:
            if has_flex_grow and s.flex_grow > 0 and not parent_is_row:
                h = 0
            else:
                h = min(ih + s.v_padding + s.v_border, available_h)
        if s.max_width is not None:
            w = min(w, _resolve_dimension(s.max_width, available_w))
        if s.max_height is not None:
            h = min(h, _resolve_dimension(s.max_height, available_h))
        if s.min_width is not None:
            w = max(w, float(s.min_width))
        if s.min_height is not None:
            h = max(h, float(s.min_height))
        return LayoutBox(node=node, width=w, height=h)

    # Box node
    if w is None:
        if has_flex_grow and s.flex_grow > 0 and parent_is_row:
            w = 0  # will be filled by flex_grow
        else:
            w = available_w
    if h is None:
        if has_flex_grow and s.flex_grow > 0 and not parent_is_row:
            h = 0  # will be filled by flex_grow
        else:
            h = available_h
    if s.min_width is not None:
        w = max(w, float(s.min_width))
    if s.min_height is not None:
        h = max(h, float(s.min_height))
    if s.max_width is not None:
        w = min(w, _resolve_dimension(s.max_width, available_w))
    if s.max_height is not None:
        h = min(h, _resolve_dimension(s.max_height, available_h))
    # min wins over max
    if s.min_width is not None:
        w = max(w, float(s.min_width))
    if s.min_height is not None:
        h = max(h, float(s.min_height))

    layout = LayoutBox(node=node, width=w, height=h)

    if not node.children:
        return layout

    # Content area (inside border + padding)
    content_x = s.padding_left + s.border_width
    content_y = s.padding_top + s.border_width
    content_w = max(0, w - s.h_padding - s.h_border)
    content_h = max(0, h - s.v_padding - s.v_border)

    is_row = s.flex_direction == "row"

    # Check if any child has flex_grow
    any_grow = any(c.style.flex_grow > 0 for c in node.children)

    # First pass: layout children to get their sizes
    child_layouts = []
    for child in node.children:
        cs = child.style
        child_avail_w = max(0, content_w - cs.h_margin)
        child_avail_h = max(0, content_h - cs.v_margin)
        cl = _layout_node(child, child_avail_w, child_avail_h, parent_is_row=is_row, has_flex_grow=any_grow)
        child_layouts.append(cl)

    # Calculate total fixed size and flex_grow
    total_fixed = 0
    total_grow = 0.0
    gap = s.gap
    num_children = len(child_layouts)

    for cl in child_layouts:
        cs = cl.node.style
        if is_row:
            total_fixed += cl.width + cs.h_margin
        else:
            total_fixed += cl.height + cs.v_margin
        total_grow += cs.flex_grow

    total_gaps = gap * max(0, num_children - 1)
    main_size = content_w if is_row else content_h
    remaining = max(0, main_size - total_fixed - total_gaps)

    # Distribute flex_grow
    if total_grow > 0:
        for cl in child_layouts:
            cs = cl.node.style
            if cs.flex_grow > 0:
                extra = remaining * (cs.flex_grow / total_grow)
                if is_row:
                    cl.width += extra
                else:
                    cl.height += extra
        # Enforce max_width/max_height after flex_grow distribution
        for cl in child_layouts:
            cs = cl.node.style
            if cs.flex_grow > 0:
                child_avail_w = max(0, content_w - cs.h_margin)
                child_avail_h = max(0, content_h - cs.v_margin)
                if cs.max_width is not None:
                    cl.width = min(cl.width, _resolve_dimension(cs.max_width, child_avail_w))
                if cs.max_height is not None:
                    cl.height = min(cl.height, _resolve_dimension(cs.max_height, child_avail_h))
        # After distributing grow, re-layout children that grew (to lay out their children with correct size)
        for cl in child_layouts:
            cs = cl.node.style
            if cs.flex_grow > 0 and isinstance(cl.node, Box) and cl.node.children:
                new_cl = _layout_node(cl.node, cl.width, cl.height, parent_is_row=is_row, has_flex_grow=False)
                cl.children = new_cl.children
                # Keep the grow-assigned width/height
                # But update the non-main-axis dimension if it was auto
                if is_row and cs.height is None:
                    pass  # keep h from first pass
                elif not is_row and cs.width is None:
                    pass

    # Handle align_items=stretch
    for cl in child_layouts:
        cs = cl.node.style
        if s.align_items == "stretch":
            if is_row:
                if cl.node.style.height is None:
                    cl.height = max(0, content_h - cs.v_margin)
            else:
                if cl.node.style.width is None:
                    cl.width = max(0, content_w - cs.h_margin)

    # Compute main-axis sizes for justify
    total_main = 0
    for cl in child_layouts:
        cs = cl.node.style
        if is_row:
            total_main += cl.width + cs.h_margin
        else:
            total_main += cl.height + cs.v_margin

    total_main_with_gap = total_main + total_gaps

    # Justify content
    justify = s.justify_content
    main_offset = 0.0
    extra_gap = 0.0

    if justify == "start":
        main_offset = 0
    elif justify == "center":
        main_offset = (main_size - total_main_with_gap) / 2
    elif justify == "end":
        main_offset = main_size - total_main_with_gap
    elif justify == "space_between":
        if num_children <= 1:
            main_offset = (main_size - total_main) / 2
            extra_gap = 0
        else:
            space = main_size - total_main
            extra_gap = space / (num_children - 1)
            main_offset = 0
    elif justify == "space_around":
        if num_children == 0:
            main_offset = 0
        else:
            space = main_size - total_main
            slot = space / num_children
            main_offset = slot / 2
            extra_gap = slot

    # Position children
    cursor = main_offset
    for cl in child_layouts:
        cs = cl.node.style

        if is_row:
            cl.x = content_x + cursor + cs.margin_left
            cursor += cl.width + cs.h_margin
        else:
            cl.y = content_y + cursor + cs.margin_top
            cursor += cl.height + cs.v_margin

        # Add gap/extra_gap
        if justify == "space_between" and num_children > 1:
            cursor += extra_gap
        elif justify == "space_around":
            cursor += extra_gap
        else:
            cursor += gap

        # Cross axis position
        cross_size = content_h if is_row else content_w
        if is_row:
            child_cross = cl.height + cs.v_margin
            if s.align_items == "start":
                cl.y = content_y + cs.margin_top
            elif s.align_items == "center":
                cl.y = content_y + (cross_size - child_cross) / 2 + cs.margin_top
            elif s.align_items == "end":
                cl.y = content_y + cross_size - child_cross + cs.margin_top
            elif s.align_items == "stretch":
                cl.y = content_y + cs.margin_top
            else:
                cl.y = content_y + cs.margin_top
        else:
            child_cross = cl.width + cs.h_margin
            if s.align_items == "start":
                cl.x = content_x + cs.margin_left
            elif s.align_items == "center":
                cl.x = content_x + (cross_size - child_cross) / 2 + cs.margin_left
            elif s.align_items == "end":
                cl.x = content_x + cross_size - child_cross + cs.margin_left
            elif s.align_items == "stretch":
                cl.x = content_x + cs.margin_left
            else:
                cl.x = content_x + cs.margin_left

        layout.children.append(cl)

    return layout
