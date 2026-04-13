from __future__ import annotations

from PIL import Image, ImageDraw

from .fonts import load_font
from .layout import LayoutBox, compute_layout
from .nodes import Box, Img, Text
from .style import Style

Node = Box | Text | Img


def render(node: Node, width: int, height: int, background: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Render a node tree to a Pillow Image of the given dimensions."""
    layout = compute_layout(node, float(width), float(height))
    canvas = Image.new("RGBA", (width, height), background + (255,))
    _draw_layout(canvas, layout, 0, 0)
    return canvas.convert("RGB")


def _draw_layout(canvas: Image.Image, lb: LayoutBox, offset_x: float, offset_y: float):
    """Recursively draw a LayoutBox tree onto the canvas."""
    x = offset_x + lb.x
    y = offset_y + lb.y
    w = lb.width
    h = lb.height
    node = lb.node
    s = node.style

    if isinstance(node, Box):
        _draw_box(canvas, node, x, y, w, h)
        clip = s.overflow == "hidden"
        if clip:
            # Render children to a temp image and paste clipped
            temp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            for child_lb in lb.children:
                _draw_layout(temp, child_lb, x, y)
            # Clip to box bounds
            ix, iy = int(x), int(y)
            iw, ih = int(w), int(h)
            # Clamp to canvas bounds
            cx1 = max(0, ix)
            cy1 = max(0, iy)
            cx2 = min(canvas.width, ix + iw)
            cy2 = min(canvas.height, iy + ih)
            if cx2 > cx1 and cy2 > cy1:
                region = temp.crop((cx1, cy1, cx2, cy2))
                canvas.paste(region, (cx1, cy1), region)
        else:
            for child_lb in lb.children:
                _draw_layout(canvas, child_lb, x, y)

    elif isinstance(node, Text):
        _draw_text(canvas, lb, x, y, w, h)

    elif isinstance(node, Img):
        _draw_img(canvas, node, x, y, w, h)


def _draw_box(canvas: Image.Image, node: Box, x: float, y: float, w: float, h: float):
    """Draw box background and border."""
    s = node.style
    ix, iy, iw, ih = int(x), int(y), int(w), int(h)
    if iw <= 0 or ih <= 0:
        return
    draw = ImageDraw.Draw(canvas)

    # Background (fills the entire border-box area)
    if s.background is not None:
        draw.rectangle([ix, iy, ix + iw - 1, iy + ih - 1], fill=s.background + (255,))

    # Border
    bw = s.border_width
    if bw > 0:
        bc = s.border_color + (255,)
        # Top border
        draw.rectangle([ix, iy, ix + iw - 1, iy + bw - 1], fill=bc)
        # Bottom border
        draw.rectangle([ix, iy + ih - bw, ix + iw - 1, iy + ih - 1], fill=bc)
        # Left border
        draw.rectangle([ix, iy, ix + bw - 1, iy + ih - 1], fill=bc)
        # Right border
        draw.rectangle([ix + iw - bw, iy, ix + iw - 1, iy + ih - 1], fill=bc)


def _draw_text(canvas: Image.Image, lb: LayoutBox, x: float, y: float, w: float, h: float):
    """Draw text content."""
    node = lb.node
    if not node.content:
        return

    s = node.style
    font_size = lb.resolved_font_size or s.font_size
    font = load_font(size=font_size)
    draw = ImageDraw.Draw(canvas)

    bbox = font.getbbox(node.content)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Content area
    cx = x + s.padding_left + s.border_width
    cy = y + s.padding_top + s.border_width
    cw = max(0, w - s.h_padding - s.h_border)
    ch = max(0, h - s.v_padding - s.v_border)

    # Horizontal alignment
    if s.text_align == "center":
        tx = cx + (cw - text_w) / 2
    elif s.text_align == "right":
        tx = cx + cw - text_w
    else:
        tx = cx

    # Vertical center
    ty = cy + (ch - text_h) / 2

    # Adjust for font bbox offset
    tx -= bbox[0]
    ty -= bbox[1]

    if text_w <= cw:
        # Fast path: text fits, draw directly
        draw.text((int(tx), int(ty)), node.content, fill=s.font_color + (255,), font=font)
    else:
        # Slow path: draw to temp, clip to content area
        temp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp)
        temp_draw.text((int(tx), int(ty)), node.content, fill=s.font_color + (255,), font=font)
        icx, icy = int(cx), int(cy)
        icw, ich = int(cw), int(ch)
        cx2 = min(canvas.width, icx + icw)
        cy2 = min(canvas.height, icy + ich)
        if cx2 > icx and cy2 > icy:
            region = temp.crop((icx, icy, cx2, cy2))
            canvas.paste(region, (icx, icy), region)


def _draw_img(canvas: Image.Image, node: Img, x: float, y: float, w: float, h: float):
    """Draw an image with object-fit semantics."""
    img = node.load_image()
    if img is None:
        return

    s = node.style
    # Content area
    cx = x + s.padding_left + s.border_width
    cy = y + s.padding_top + s.border_width
    cw = max(0, w - s.h_padding - s.h_border)
    ch = max(0, h - s.v_padding - s.v_border)

    icw, ich = int(cw), int(ch)
    if icw <= 0 or ich <= 0:
        return

    src_w, src_h = img.size
    resample = Image.NEAREST if s.image_rendering == "pixelated" else Image.LANCZOS

    if s.object_fit == "fill":
        fitted = img.resize((icw, ich), resample)
        _paste_img(canvas, fitted, int(cx), int(cy))
    elif s.object_fit == "cover":
        # Scale to fill, then crop center
        scale = max(icw / src_w, ich / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        scaled = img.resize((new_w, new_h), resample)
        # Crop to content size, centered
        crop_x = (new_w - icw) // 2
        crop_y = (new_h - ich) // 2
        cropped = scaled.crop((crop_x, crop_y, crop_x + icw, crop_y + ich))
        _paste_img(canvas, cropped, int(cx), int(cy))
    else:  # contain
        scale = min(icw / src_w, ich / src_h) if src_w > 0 and src_h > 0 else 1
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        if new_w <= 0 or new_h <= 0:
            return
        scaled = img.resize((new_w, new_h), resample)
        # Center in content area
        paste_x = int(cx + (icw - new_w) / 2)
        paste_y = int(cy + (ich - new_h) / 2)
        _paste_img(canvas, scaled, paste_x, paste_y)


def _paste_img(canvas: Image.Image, img: Image.Image, x: int, y: int):
    """Paste an image onto the canvas, handling RGBA alpha compositing."""
    if img.mode == "RGBA":
        canvas.paste(img, (x, y), img)
    else:
        canvas.paste(img, (x, y))
