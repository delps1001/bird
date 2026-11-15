"""Download + cut out candidate photos and build a numbered contact sheet per species.

usage: python cands.py names.txt [k]     (names.txt: one filename stem per line, e.g. eastern_bluebird)
Writes work/cutouts/<name>/c0..c<k-1>.png and sheet.png.  View the sheet, pick the best
side-profile cutout and record it in picks.py.
"""
import sys
from PIL import Image, ImageDraw
import fetch
from common import CUTS

def run(name, k=12, T=200, cols=4):
    out = CUTS / name; out.mkdir(exist_ok=True)
    if (out / "sheet.png").exists():
        return
    urls = fetch.candidates(fetch.labels[name], k + 8)[:k]
    sheet = Image.new("RGB", (cols * T, ((len(urls) + cols - 1) // cols) * T), (210, 210, 210))
    for i, u in enumerate(urls):
        try:
            cut = fetch.cutout(u); cut.save(out / f"c{i}.png")
            t = cut.copy(); t.thumbnail((T, T)); sheet.paste(t, ((i % cols) * T, (i // cols) * T), t)
            ImageDraw.Draw(sheet).text(((i % cols) * T + 4, (i // cols) * T + 2), str(i), fill=(255, 0, 0))
        except Exception as e:
            print(name, i, e, flush=True)
    sheet.save(out / "sheet.png"); print("done", name, flush=True)

if __name__ == "__main__":
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    for n in open(sys.argv[1]).read().split():
        try: run(n, k)
        except Exception as e: print("FAIL", n, e, flush=True)
