"""Use a photo you supply (instead of downloading iNaturalist candidates) as the reference for one bird.

usage: python from_photo.py <name> <photo> [--idx 1] [--rembg]

Cuts the bird out and writes work/cutouts/<name>/c<idx>.png, ready for run_gen.py / install.py.
By default the background is removed by flood-filling near-white/near-uniform pixels from the image
border (good for cutout-style photos on white). Pass --rembg for busy backgrounds (needs `pip install
rembg`, which downloads a model on first use).
Afterwards add to your picks file:  PICKS = {"<name>": (<idx>, <flip>)}   flip=1 if the bird faces right.
"""
import argparse
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from common import CUTS

ap = argparse.ArgumentParser()
ap.add_argument("name"); ap.add_argument("photo")
ap.add_argument("--idx", type=int, default=1); ap.add_argument("--rembg", action="store_true")
ap.add_argument("--tol", type=float, default=40, help="colour distance from the border colour treated as background")
a = ap.parse_args()

img = Image.open(a.photo).convert("RGBA")
if a.rembg:
    from rembg import remove
    cut = remove(img)
else:
    rgb = np.array(img.convert("RGB")).astype(float)
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    near = np.linalg.norm(rgb - bg, axis=2) < a.tol
    lab, _ = ndi.label(near)
    edge_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgmask = np.isin(lab, list(edge_labels))
    fg = ndi.binary_fill_holes(~bgmask)           # keep interior highlights
    fg = ndi.binary_opening(fg, iterations=1)
    lab2, k = ndi.label(fg)                      # keep the largest blob only
    if k > 1:
        sizes = ndi.sum(fg, lab2, range(1, k + 1)); fg = lab2 == 1 + int(np.argmax(sizes))
    alpha = ndi.gaussian_filter(fg.astype(float), 0.7)
    arr = np.array(img); arr[..., 3] = (alpha * 255).astype("uint8"); cut = Image.fromarray(arr, "RGBA")

out = CUTS / a.name; out.mkdir(parents=True, exist_ok=True)
cut.save(out / f"c{a.idx}.png"); print("wrote", out / f"c{a.idx}.png")
