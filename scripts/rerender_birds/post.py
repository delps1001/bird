"""Silhouette cleanup: keep only generated pixels near the reference silhouette."""
import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as ndi
import bf
from common import CUTS

def ref_mask(name, idx, flip):
    cut = Image.open(CUTS / name / f"c{idx}.png")
    if flip: cut = ImageOps.mirror(cut)
    return np.array(bf.fit(cut).getchannel("A")) > 128

def clean(sprite, name, idx, flip, grow=5):
    """Restrict sprite to the reference silhouette grown by `grow` px and keep the main blob.
    Returns (sprite, outside_fraction); outside_fraction > ~0.1 means hallucinated twigs/sprigs."""
    a = np.array(sprite.convert("RGBA")); al = a[..., 3] > 128
    allowed = ndi.binary_dilation(ref_mask(name, idx, flip), iterations=grow)
    outside = (al & ~allowed).sum() / max(1, al.sum())
    keep = al & allowed
    lab, k = ndi.label(keep, structure=np.ones((3, 3)))
    if k > 1:
        sizes = ndi.sum(keep, lab, range(1, k + 1))
        keep = np.isin(lab, 1 + np.where(sizes >= max(sizes.max() * 0.12, 6))[0])
    a[..., 3] = np.where(keep, 255, 0)
    return Image.fromarray(a, "RGBA"), float(outside)
