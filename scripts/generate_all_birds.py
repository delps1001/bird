#!/usr/bin/env python3
"""Generate pixel art for all birds in SPECIES_LIST.txt.

Reads species from assets/birds/SPECIES_LIST.txt, generates 64x64 pixel art
via Pixellab API, and saves PNGs to assets/birds/.

Skips birds that already have a PNG file, so it's safe to re-run.

Usage:
    1. Ensure .env has: PIXELLAB_SECRET=your-key-here
    2. python scripts/generate_all_birds.py
    3. Re-run to retry any failures (already-generated birds are skipped)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from pixellab import Client

# --- Config ---
SPECIES_LIST = Path("assets/birds/SPECIES_LIST.txt")
OUTPUT_DIR = Path("assets/birds")
SIZE = 64

PROMPT_TEMPLATE = (
    "{size}x{size} pixel art of a {bird} bird species, "
    "ornithology illustration style, "
    "realistic plumage colors and shading, "
    "full body side profile, "
    "transparent background"
)

# Pause between API calls to avoid rate limits
DELAY_BETWEEN_CALLS = 1.0


def filename_to_bird_name(filename: str) -> str:
    """Convert 'red_tailed_hawk.png' -> 'Red-tailed Hawk'."""
    name = filename.removesuffix(".png")
    # Restore apostrophes (already present in filenames like "bachman's_sparrow")
    # Convert underscores to spaces and title-case
    words = name.split("_")
    return " ".join(w.capitalize() if not w.endswith("'s") else w for w in words)


def main() -> None:
    print("=" * 60)
    print("  Bird Pixel Art Generator")
    print("=" * 60)
    print()

    print(f"Reading species list from: {SPECIES_LIST}")
    if not SPECIES_LIST.exists():
        raise SystemExit(f"ERROR: Species list not found: {SPECIES_LIST}")

    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Image size: {SIZE}x{SIZE}")
    print()

    print("Loading API client from .env...")
    client = Client.from_env_file(".env")
    print("  API client loaded successfully.")
    print()

    # Read species list
    print("Parsing species list...")
    lines = SPECIES_LIST.read_text().strip().splitlines()
    species = [line.strip() for line in lines if line.strip()]
    total = len(species)
    print(f"  Found {total} species in list.")
    print()

    # Check which already exist
    print("Checking for existing images...")
    existing = {f for f in species if (OUTPUT_DIR / f).exists()}
    to_generate = [f for f in species if f not in existing]
    print(f"  Already generated: {len(existing)}")
    print(f"  Remaining to generate: {len(to_generate)}")
    if existing:
        print(f"  (skipping existing files)")
    print()

    if not to_generate:
        print("All birds already generated! Nothing to do.")
        return

    estimated_time = len(to_generate) * (DELAY_BETWEEN_CALLS + 2)  # ~2s per API call + delay
    print(f"Estimated time: ~{estimated_time / 60:.0f} minutes")
    print(f"Delay between calls: {DELAY_BETWEEN_CALLS}s")
    print()
    print("-" * 60)

    successes = 0
    failures = []
    start_time = time.time()

    for i, filename in enumerate(to_generate, 1):
        bird_name = filename_to_bird_name(filename)
        out_path = OUTPUT_DIR / filename
        prompt = PROMPT_TEMPLATE.format(size=SIZE, bird=bird_name)

        elapsed = time.time() - start_time
        if i > 1:
            avg_per_bird = elapsed / (i - 1)
            remaining = avg_per_bird * (len(to_generate) - i + 1)
            eta = f" | ETA: {remaining / 60:.1f}min"
        else:
            eta = ""

        print(f"\n[{i}/{len(to_generate)}] {bird_name}{eta}")
        print(f"  File: {filename}")
        print(f"  Prompt: {prompt}")
        print(f"  Calling Pixellab API...")

        call_start = time.time()
        try:
            result = client.generate_image_pixflux(
                description=prompt,
                image_size={"width": SIZE, "height": SIZE},
                no_background=True,
            )
            call_duration = time.time() - call_start
            print(f"  API responded in {call_duration:.1f}s")

            print(f"  Converting to PIL image...")
            img = result.image.pil_image()
            print(f"  Image size: {img.size}, mode: {img.mode}")

            print(f"  Saving to {out_path}...")
            img.save(str(out_path))
            file_size = out_path.stat().st_size
            print(f"  Saved! ({file_size:,} bytes)")

            successes += 1

        except Exception as e:
            call_duration = time.time() - call_start
            failures.append((filename, str(e)))
            print(f"  FAILED after {call_duration:.1f}s: {e}")

        print(f"  Progress: {successes} ok, {len(failures)} failed, {len(to_generate) - i} remaining")

        # Rate limit
        if i < len(to_generate):
            print(f"  Waiting {DELAY_BETWEEN_CALLS}s before next call...")
            time.sleep(DELAY_BETWEEN_CALLS)

    # Summary
    total_time = time.time() - start_time
    print()
    print("=" * 60)
    print("  COMPLETE")
    print("=" * 60)
    print(f"  Total time: {total_time / 60:.1f} minutes")
    print(f"  Successful: {successes}/{len(to_generate)}")
    print(f"  Failed: {len(failures)}/{len(to_generate)}")
    if successes:
        print(f"  Avg time per bird: {total_time / successes:.1f}s")
    print()

    if failures:
        print(f"FAILURES (re-run script to retry these):")
        for fname, err in failures:
            bird = filename_to_bird_name(fname)
            print(f"  {bird} ({fname}): {err}")
        print()

    total_generated = len(existing) + successes
    print(f"Overall: {total_generated}/{total} species have pixel art.")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
