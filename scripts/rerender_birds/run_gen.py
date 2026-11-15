"""Generate 64x64 sprites with Pixellab bitforge, using the photo cutout as init image.

usage: python run_gen.py [--seeds 1,2] [--retry] [--only a,b] [--picks picks.py]
--retry uses a harder negative prompt, init strength 330 and "single bird only" (use seeds 3,4,5).
Stops if the account balance drops below --min-balance (default $0.40).  ~$0.01 per call.
"""
import argparse, sys, time
from PIL import Image, ImageOps
import bf
from common import CUTS, GEN, load_picks

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default="1,2"); ap.add_argument("--retry", action="store_true")
ap.add_argument("--only", default=""); ap.add_argument("--picks", default="picks.py")
ap.add_argument("--min-balance", type=float, default=0.40)
a = ap.parse_args()
PICKS, FRONT, VERTICAL, FLYING = load_picks(a.picks)
only = set(a.only.split(",")) if a.only else None
NEG = "plants, leaves, branches, tree, snow, ground, antlers, extra heads, multiple birds, text, background"
if a.retry:
    NEG = ("twig, stick, branch, sprig, leaf, plant, grass, feather plume, curved line, antenna, extra tail, tree, snow, "
           "ground, antlers, extra heads, multiple birds, text, background, floating objects")
client = bf.client(); calls = 0
for name, (idx, flip) in PICKS.items():
    if only and name not in only: continue
    cut = Image.open(CUTS / name / f"c{idx}.png")
    if flip: cut = ImageOps.mirror(cut)
    common = name.replace("_", " ").title().replace("'S", "'s")
    view = "front view" if name in FRONT else "in flight" if name in FLYING else "perched upright" if name in VERTICAL else "side profile"
    for seed in [int(s) for s in a.seeds.split(",")]:
        out = GEN / f"{name}_s{seed}.png"
        if out.exists(): continue
        if calls % 25 == 0:
            bal = client.get_balance().usd; print("balance", round(bal, 2), flush=True)
            if bal < a.min_balance: sys.exit("low balance, stopping")
        calls += 1
        kw = dict(description=f"{common}, pixel art, {view}, accurate plumage colors" + (", single bird only" if a.retry else ""),
                  negative_description=NEG, image_size={"width": 64, "height": 64}, no_background=True, seed=seed,
                  outline="single color black outline", shading="medium shading", detail="medium detail",
                  init_image=bf.fit(cut), init_image_strength=330 if a.retry else 320)
        if name not in FRONT: kw["direction"] = "west"
        for attempt in range(4):
            try:
                client.generate_image_bitforge(**kw).image.pil_image().save(out); print("ok", name, seed, flush=True); break
            except Exception as e:
                print("FAIL", name, seed, str(e)[:60], flush=True)
                if "429" in str(e): time.sleep(8 * (attempt + 1))
                else: break
