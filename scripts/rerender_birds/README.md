# Re-rendering bird sprites from reference photos

Pipeline used to re-render the `assets/birds/*.png` sprites (64x64 RGBA, bird facing left):

1. `cands.py` - for each species, download research-grade iNaturalist photos, cut the bird out with `rembg`
   and write a numbered contact sheet (`work/cutouts/<name>/sheet.png`).
2. Look at the sheet, pick the best whole-bird side profile and note it in a `picks.py`
   (`PICKS = {"name": (candidate_index, flip)}`, `flip=1` when the bird faces right; optional
   `FRONT` / `VERTICAL` / `FLYING` sets change the prompt wording). See `picks_remaining.py` for the real data.
3. `run_gen.py` - Pixellab bitforge generation with the photo as init image (seeds 1,2; `--retry --seeds 3,4,5`
   for failures). Stops when the balance is below $0.40.
4. Review the outputs, choose a seed per bird in a `choice.txt` (`name:seed` per line) and run `install.py`,
   which applies the silhouette cleanup (`post.py`: keep only pixels near the reference silhouette, drop stray
   twigs/sprigs) and writes `assets/birds/<name>.png`.

## Running

```
pip install pillow numpy scipy scikit-image rembg pixellab requests
echo "PIXELLAB_SECRET=..." >> .env          # repo root, not committed
cd scripts/rerender_birds
python cands.py names.txt                   # names.txt: one filename stem per line
python run_gen.py --picks picks.py --seeds 1,2
python run_gen.py --picks picks.py --retry --seeds 3,4,5 --only some_bird
python install.py choice.txt picks.py
```

Work files go to `./work` (override with `BIRD_WORK`); the repo root can be overridden with `BIRD_REPO`.
Each generation costs about $0.01.
