"""Deterministic alternative to run_gen.py: shrink the reference cutout straight to a 64x64 sprite.

usage: python pixelize.py <name> [--idx 1] [--flip 1] [--fit 62] [--colors 16] [--sat 1.25] [--contrast 1.2]
                          [--erode 3] [--out preview.png] [--install]

Reads work/cutouts/<name>/c<idx>.png (see from_photo.py / cands.py), mirrors it when --flip 1 (bird faces
right), erodes the alpha edge (kills the light halo from the cutout), box-downscales, boosts colour,
quantizes to a small palette and adds a 1px dark outline. Nothing is hallucinated, so thin bills and long
legs survive (where bitforge drops them). Without --install it only writes the preview (default
work/<name>_pixelized.png); with --install it writes assets/birds/<name>.png.
"""
import argparse
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from scipy import ndimage as ndi
from common import CUTS, WORK, SPRITES

ap = argparse.ArgumentParser()
ap.add_argument("name"); ap.add_argument("--idx", type=int, default=1); ap.add_argument("--flip", type=int, default=0)
ap.add_argument("--fit", type=int, default=62); ap.add_argument("--colors", type=int, default=16)
ap.add_argument("--sat", type=float, default=1.25); ap.add_argument("--contrast", type=float, default=1.2)
ap.add_argument("--erode", type=int, default=3); ap.add_argument("--out"); ap.add_argument("--install", action="store_true")
a = ap.parse_args()

cut = Image.open(CUTS / a.name / f"c{a.idx}.png").convert("RGBA")
if a.flip: cut = ImageOps.mirror(cut)
alpha = ndi.binary_erosion(np.array(cut.getchannel("A")) > 128, iterations=a.erode)
cut.putalpha(Image.fromarray((alpha * 255).astype("uint8")))
cut = cut.crop(cut.getchannel("A").getbbox())
w, h = cut.size; s = a.fit / max(w, h); nw, nh = round(w * s), round(h * s)
rgb = np.array(cut.convert("RGB")).astype(float); al = np.array(cut.getchannel("A")).astype(float) / 255
pm = Image.fromarray(np.dstack([rgb * al[..., None], al * 255]).astype("uint8"), "RGBA").resize((nw, nh), Image.BOX)
p = np.array(pm).astype(float); al = p[..., 3] / 255
col = (p[..., :3] / np.maximum(al[..., None], 1e-3)).clip(0, 255).astype("uint8")
im = ImageEnhance.Contrast(ImageEnhance.Color(Image.fromarray(col, "RGB")).enhance(a.sat)).enhance(a.contrast)
arr = np.array(im.quantize(a.colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB"))
full = np.zeros((nh + 2, nw + 2), bool); full[1:-1, 1:-1] = al > 0.5
ring = ndi.binary_dilation(full, structure=np.ones((3, 3))) & ~full
o = np.zeros((nh + 2, nw + 2, 4), "uint8"); o[1:-1, 1:-1, :3] = arr; o[full, 3] = 255; o[ring] = (40, 28, 20, 255)
sp = Image.fromarray(o, "RGBA"); canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
canvas.paste(sp, ((64 - sp.width) // 2, 64 - sp.height))
if a.install: canvas.save(SPRITES / f"{a.name}.png"); print("installed", SPRITES / f"{a.name}.png")
else:
    out = a.out or WORK / f"{a.name}_pixelized.png"; canvas.save(out); print("preview", out)
