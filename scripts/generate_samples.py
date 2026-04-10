#!/usr/bin/env python3
"""Generate a few sample bird pixel art images to evaluate quality.

Usage:
    1. Create .env in project root with: PIXELLAB_SECRET=your-key-here
    2. pip install pixellab python-dotenv
    3. python scripts/generate_samples.py
"""
from __future__ import annotations

from pathlib import Path

from pixellab import Client

# --- Config ---
SAMPLE_BIRDS = [
    "American Robin",
    "Northern Cardinal",
    # "Blue Jay",
    # "Bald Eagle",
    # "Ruby-throated Hummingbird",
]
SIZE = 64
OUTPUT_DIR = Path("output/samples")

PROMPT_TEMPLATE = (
    "{size}x{size} pixel art of a {bird} bird species, "
    "ornithology illustration style, "
    "realistic plumage colors and shading, "
    "full body side profile perched on a branch, "
    "transparent background"
)


def main() -> None:
    client = Client.from_env_file(".env")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for bird in SAMPLE_BIRDS:
        prompt = PROMPT_TEMPLATE.format(size=SIZE, bird=bird)
        filename = bird.lower().replace(" ", "_").replace("-", "_").replace("'", "'")
        out_path = OUTPUT_DIR / f"{filename}.png"

        print(f"Generating: {bird}...")
        print(f"  Prompt: {prompt}")

        try:
            result = client.generate_image_pixflux(
                description=prompt,
                image_size={"width": SIZE, "height": SIZE},
                no_background=True,
            )
            result.image.pil_image().save(str(out_path))
            print(f"  Saved: {out_path}")

        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    print(f"Done! Check {OUTPUT_DIR}/ for results.")


if __name__ == "__main__":
    main()
