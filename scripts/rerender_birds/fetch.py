"""Fetch research-grade iNaturalist photos for a species and cut the bird out (rembg)."""
import io, re, requests
from PIL import Image
from rembg import remove, new_session
from common import LABELS

labels = {}
for l in LABELS.read_text().splitlines():
    sci, com = l.split("_", 1)
    labels[re.sub(r"[ \-]", "_", com.lower())] = sci
_sess = None
HDR = {"User-Agent": "bird-sprite-research/0.1"}

def session():
    global _sess
    if _sess is None:
        _sess = new_session("isnet-general-use")
    return _sess

def candidates(sci, n=12):
    """Photo URLs (large) of adult research-grade observations of species `sci`."""
    res = requests.get("https://api.inaturalist.org/v1/taxa", params={"q": sci, "rank": "species", "per_page": 10}, headers=HDR).json()["results"]
    birds = [x for x in res if x.get("iconic_taxon_name") == "Aves"]
    t = ([x for x in birds if x["name"].lower() == sci.lower()] or birds or res)[0]
    if t["name"].lower() != sci.lower():
        print("TAXON MISMATCH", sci, "->", t["name"], flush=True)   # taxonomy synonym; eyeball the sheet
    r = requests.get("https://api.inaturalist.org/v1/observations", params={
        "taxon_id": t["id"], "quality_grade": "research", "photo_license": "cc0,cc-by,cc-by-sa",
        "per_page": n, "order_by": "votes", "term_id": 1, "term_value_id": 2, "photos": "true"}, headers=HDR).json()["results"]
    return [o["photos"][0]["url"].replace("square", "large") for o in r if o["photos"]]

def cutout(url):
    im = Image.open(io.BytesIO(requests.get(url, headers=HDR, timeout=20).content)).convert("RGB")
    return remove(im, session=session(), post_process_mask=True)
