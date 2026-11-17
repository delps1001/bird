---
name: update-bird-image
description: Regenerate one bird's 64x64 e-ink sprite (assets/birds/<name>.png) from a reference photo the user supplies, then open a PR. Use when the user says things like "regenerate the <bird> image with this photo", "update the <bird> sprite", or attaches a bird photo for the birdpi frame.
---

# Update a bird sprite from a reference photo

Sprites are 64x64 RGBA PNGs in `assets/birds/<name>.png` (name = lowercase, underscores, e.g. `american_woodcock`), bird facing **left**. The pipeline lives in `scripts/rerender_birds/` (read its README for the background); this skill is the single-bird fast path.

## Steps

1. **Identify the target.** Confirm `assets/birds/<name>.png` exists (`ls assets/birds | grep <word>`). Find the photo path (an attached image is saved under `~/.claude/uploads/...`; the path is given in the conversation). Look at the photo: note whether the bird faces left or right (`flip=1` if it faces right).

2. **Set up a scratch env** (once per session, in the scratchpad dir, never in the repo):
   ```
   python3 -m venv v && ./v/bin/pip install -q pillow numpy scipy scikit-image pixellab requests
   ```
   `PIXELLAB_SECRET` must be in `<repo>/.env` (git-ignored; never print it). Each generation costs about $0.01. If the key is missing, ask the user.

3. **Cut out the bird** (run from a scratch dir; `work/` is created relative to the cwd):
   ```
   mkdir -p work && cd work
   ../v/bin/python -W ignore <repo>/scripts/rerender_birds/from_photo.py <name> <photo>
   ```
   This writes `work/work/cutouts/<name>/c1.png` (set `BIRD_WORK` to avoid the nested `work/work`). Read the cutout image and check it is a clean whole-bird silhouette. For busy backgrounds add `--rembg`, or raise/lower `--tol`.

4. **Write `picks.py`** (only needed for the AI route in step 6) in the same scratch dir: `PICKS = {"<name>": (1, <flip>)}`. Add `FRONT`/`VERTICAL`/`FLYING` sets only if the pose is not a side profile.

5. **Pixelize (default).** Deterministic, nothing hallucinated; keeps thin bills, long legs and the real plumage pattern:
   ```
   ../v/bin/python -W ignore <repo>/scripts/rerender_birds/pixelize.py <name> --idx 1 --flip <0|1>
   ```
   Preview is written to `work/<name>_pixelized.png`; tune `--sat` (1.25), `--contrast` (1.2), `--colors` (16), `--fit` (62), `--erode` (3) and show the user an upscaled (6x NEAREST) sheet next to the current sprite. Add `--install` to write `assets/birds/<name>.png`. Do not auto-pick; let the user choose the variant.

6. **AI alternative (only if the user wants hand-drawn look, ~$0.01/call).** `run_gen.py --picks picks.py --seeds 1,2,3,4` (add `--retry --seeds 5,6,7,8` for twigs/extras), review a contact sheet of the seeds, then `install.py choice.txt picks.py`. Bitforge drops 1-2px features: the 2026-11 woodcock attempt (8 seeds) lost the bill every time, which is why pixelize is the default.

7. **Verify** the file is 64x64 RGBA and, if tests reference sprites, run `python -m pytest -q`. View the final PNG upscaled.

8. **PR.** Branch off the up-to-date default branch (`git fetch origin && git switch -c update-<name>-sprite origin/main`), commit only `assets/birds/<name>.png` (plus pipeline changes if any) with a short message, push, and open a PR with `gh pr create`. In the body, include before/after description and the reference photo source. Only open the PR when the user has asked.

## Deploying to the frame (only if asked)

`ssh birdpi`, `git pull --ff-only` in `~/birdpi/bird`, `sudo systemctl restart bird-listener` (e-ink redraw takes ~50 s).
