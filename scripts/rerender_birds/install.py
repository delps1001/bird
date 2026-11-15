"""Clean the chosen seeds and write them to assets/birds/<name>.png.

usage: python install.py choice.txt [picks.py]     choice.txt lines: name:seed   (blank/# lines ignored)
Prints the outside fraction per sprite; > ~0.1 deserves a second look.
"""
import sys
from PIL import Image
import post
from common import GEN, SPRITES, load_picks

PICKS = load_picks(sys.argv[2] if len(sys.argv) > 2 else "picks.py")[0]
for line in open(sys.argv[1]).read().splitlines():
    line = line.strip()
    if not line or line.startswith("#"): continue
    name, seed = line.rsplit(":", 1)
    idx, flip = PICKS[name]
    sprite, out = post.clean(Image.open(GEN / f"{name}_s{seed}.png"), name, idx, flip)
    sprite.save(SPRITES / f"{name}.png"); print(name, seed, round(out, 2))
