"""Shared paths/config for the re-render pipeline.

Override with env vars: BIRD_REPO (repo root), BIRD_WORK (scratch dir for
photos / generations; default ./work next to where you run the scripts).
"""
import os, pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(os.environ.get("BIRD_REPO", HERE.parents[1]))
WORK = pathlib.Path(os.environ.get("BIRD_WORK", "work")).resolve()
CUTS = WORK / "cutouts"      # work/cutouts/<name>/c<i>.png  (+ sheet.png)
GEN = WORK / "gen"           # work/gen/<name>_s<seed>.png
SPRITES = REPO / "assets" / "birds"
LABELS = REPO / "assets" / "BirdNET_GLOBAL_6K_V2.4_Labels_en_us.txt"
for d in (CUTS, GEN):
    d.mkdir(parents=True, exist_ok=True)

def load_picks(path="picks.py"):
    """picks.py defines PICKS = {name: (candidate_index, flip_to_face_left)}
    and optional FRONT / VERTICAL / FLYING sets (prompt wording)."""
    ns = {}
    exec(pathlib.Path(path).read_text(), ns)
    return (ns["PICKS"], set(ns.get("FRONT", ())), set(ns.get("VERTICAL", ())), set(ns.get("FLYING", ())))
