"""Pixellab client + conversion of a photo cutout into the 64x64 init image."""
import numpy as np
from PIL import Image
from pixellab import Client
from common import REPO

def client():
    # reads PIXELLAB_SECRET from <repo>/.env (never printed)
    return Client.from_env_file(str(REPO / ".env"))

def fit(cut, size=64, fit=58):
    """Cutout -> size x size RGBA, bottom-centred, alpha-premultiplied downscale."""
    cut = cut.convert("RGBA")
    cut = cut.crop(cut.getchannel("A").point(lambda v: 255 if v > 128 else 0).getbbox())
    w, h = cut.size; s = fit / max(w, h); nw, nh = max(1, round(w * s)), max(1, round(h * s))
    rgb = np.array(cut.convert("RGB")).astype(float); a = np.array(cut.getchannel("A")).astype(float) / 255
    pm = Image.fromarray(np.dstack([rgb * a[..., None], a * 255]).astype("uint8"), "RGBA").resize((nw, nh), Image.LANCZOS)
    p = np.array(pm).astype(float); al = p[..., 3:] / 255
    out = np.dstack([np.where(al > 0.05, p[..., :3] / np.maximum(al, 1e-3), 0).clip(0, 255), p[..., 3:]]).astype("uint8")
    c = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    c.paste(Image.fromarray(out, "RGBA"), ((size - nw) // 2, size - nh - 3))
    return c
