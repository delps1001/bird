# Bird Listener

A Raspberry Pi application that identifies birds by sound and displays recent detections on an e-ink screen. It captures audio from a microphone, runs it through [BirdNET](https://github.com/kahst/BirdNET-Analyzer) for species identification, and renders a ranked summary to a Waveshare 7.5" e-ink display.

It can also operate in **display-only mode**, reading detections from a [BirdNET-Pi](https://github.com/mcguirepr89/BirdNET-Pi) database instead of capturing its own audio.

## Requirements

- Python 3.11 - 3.13
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- A microphone (for capture mode) or a BirdNET-Pi `birds.db` file (for display-only mode)
- Waveshare 7.5" V2 e-ink display (on Raspberry Pi) — on other platforms, output is saved as PNG files

## Installation

```bash
git clone <repo-url> && cd bird-listener
uv sync
```

## Usage

### Capture mode (microphone + analysis)

Captures audio, identifies birds with BirdNET, stores detections in a local SQLite database, and renders the display.

```bash
# Basic usage with default location
python main.py --lat 35.88 --lon -78.72

# Custom confidence threshold and refresh interval
python main.py --lat 35.88 --lon -78.72 --min-conf 0.90 --interval 60

# Single cycle (capture, analyze, render, then exit)
python main.py --lat 35.88 --lon -78.72 --once

# Use fake audio source for development/testing
python main.py --fake-audio --once
```

### Display-only mode (BirdNET-Pi database)

Reads detections from a BirdNET-Pi `birds.db` file (e.g. copied via rsync from another Pi) and renders the display. No microphone or analysis needed.

```bash
# Read from a rsync'd BirdNET-Pi database
python main.py --birdnetpi-db /mnt/birdnet/birds.db

# With custom refresh interval
python main.py --birdnetpi-db /path/to/birds.db --interval 60

# Single render then exit
python main.py --birdnetpi-db /path/to/birds.db --once
```

### CLI options

| Flag | Default | Description |
|---|---|---|
| `--lat` | `35.88` | Latitude for BirdNET location filter |
| `--lon` | `-78.72` | Longitude for BirdNET location filter |
| `--min-conf` | `0.85` | Minimum confidence threshold (0-1) |
| `--db` | `detections.db` | Path to local detections database |
| `--birdnetpi-db` | — | Path to BirdNET-Pi `birds.db` (enables display-only mode) |
| `--output` | `output` | Directory for rendered display images |
| `--assets` | `assets/birds` | Directory containing bird images |
| `--width` | `800` | Display width in pixels |
| `--height` | `480` | Display height in pixels |
| `--interval` | `30` | Seconds between refresh cycles |
| `--duration` | `15` | Audio capture duration in seconds |
| `--overlap` | `3` | Seconds of overlap between audio chunks |
| `--analyzer` | `birdnet-analyzer` | BirdNET backend (`birdnet-analyzer` or `birdnetlib`) |
| `--fake-audio` | — | Use fake audio source for testing |
| `--once` | — | Run one cycle then exit |

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with verbose output
uv run pytest -v
```

## Architecture

```
src/bird_listener/
├── audio/              # Microphone capture (and fake source for testing)
├── analysis/           # BirdNET analyzer wrappers
├── persistence/        # Detection storage (local SQLite + BirdNET-Pi read-only)
├── ranking/            # Species ranking by rarity and confidence
├── display/            # Rendering and display drivers (e-ink + file output)
├── config.py           # Application configuration
├── orchestrator.py     # Main loop (capture mode + display-only mode)
└── ports.py            # Protocol interfaces
```

The application uses a ports-and-adapters architecture. Core interfaces are defined as Python `Protocol` classes in `ports.py`, with concrete implementations swapped in at the entry point (`main.py`).
