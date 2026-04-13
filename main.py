"""Bird Listener — entry point.

Wires real implementations together and runs the main loop.
For development on macOS, uses FileDisplayDriver.
On Raspberry Pi, swap in EinkDisplayDriver.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from bird_listener.config import Config
from bird_listener.display.file_driver import FileDisplayDriver
from bird_listener.display.renderer import PillowRenderer
from bird_listener.orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Bird Listener")
    parser.add_argument("--lat", type=float, default=35.88084038419221)
    parser.add_argument("--lon", type=float, default=-78.71831163022189)
    parser.add_argument("--min-conf", type=float, default=0.85)
    parser.add_argument("--db", type=str, default="detections.db")
    parser.add_argument("--output", type=str, default="output")
    parser.add_argument("--assets", type=str, default="assets/birds")
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--overlap", type=int, default=3, help="Seconds of overlap between audio chunks")
    parser.add_argument("--fake-audio", action="store_true", help="Use fake audio source")
    parser.add_argument("--once", action="store_true", help="Run one cycle then exit")
    parser.add_argument(
        "--analyzer",
        choices=["birdnet-analyzer", "birdnetlib"],
        default="birdnet-analyzer",
        help="Which BirdNET backend to use",
    )
    parser.add_argument(
        "--birdnetpi-db",
        type=str,
        default=None,
        help="Path to BirdNET-Pi birds.db for display-only mode",
    )
    parser.add_argument(
        "--renderer",
        choices=["pillow", "grid", "picolay", "magazine", "scoreboard", "fieldguide", "filmstrip", "tower"],
        default="grid",
        help="Which display renderer to use",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--inset",
        type=float,
        default=None,
        help="Boundary inset fraction (e-ink frame cropping)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config_kwargs = dict(
        lat=args.lat,
        lon=args.lon,
        min_confidence=args.min_conf,
        display_width=args.width,
        display_height=args.height,
        assets_dir=Path(args.assets),
        output_dir=Path(args.output),
        db_path=Path(args.db),
        capture_duration_sec=args.duration,
        capture_overlap_sec=args.overlap,
        loop_interval_sec=args.interval,
        display_renderer=args.renderer,
    )
    if args.inset is not None:
        config_kwargs["boundary_inset"] = args.inset
    config = Config(**config_kwargs)

    # Display
    if config.display_renderer == "grid":
        from bird_listener.display.grid_layout import GridDisplayLayout
        from bird_listener.display.grid_renderer import GridRenderer

        grid_layout = GridDisplayLayout(inset=config.boundary_inset)
        renderer = GridRenderer(layout=grid_layout)
    elif config.display_renderer == "picolay":
        from bird_listener.display.grid_layout import GridDisplayLayout
        from bird_listener.display.grid_renderer_picolay import PicolayGridRenderer

        grid_layout = GridDisplayLayout(inset=config.boundary_inset)
        renderer = PicolayGridRenderer(layout=grid_layout)
    elif config.display_renderer == "magazine":
        from bird_listener.display.magazine_renderer import MagazineRenderer
        renderer = MagazineRenderer(inset=config.boundary_inset)
    elif config.display_renderer == "scoreboard":
        from bird_listener.display.scoreboard_renderer import ScoreboardRenderer
        renderer = ScoreboardRenderer(inset=config.boundary_inset)
    elif config.display_renderer == "fieldguide":
        from bird_listener.display.fieldguide_renderer import FieldGuideRenderer
        renderer = FieldGuideRenderer(inset=config.boundary_inset)
    elif config.display_renderer == "filmstrip":
        from bird_listener.display.filmstrip_renderer import FilmstripRenderer
        renderer = FilmstripRenderer(inset=config.boundary_inset)
    elif config.display_renderer == "tower":
        from bird_listener.display.tower_renderer import TowerRenderer
        renderer = TowerRenderer(inset=config.boundary_inset)
    else:
        renderer = PillowRenderer()
    display = FileDisplayDriver(config.output_dir)

    if args.birdnetpi_db:
        # Display-only mode: read from BirdNET-Pi's database
        from bird_listener.persistence.birdnetpi_repository import BirdNetPiRepository

        repository = BirdNetPiRepository(
            Path(args.birdnetpi_db),
            min_confidence=config.min_confidence,
        )

        orchestrator = Orchestrator(
            config=config,
            repository=repository,
            renderer=renderer,
            display=display,
        )
        orchestrator.run_display_only(once=args.once)
    else:
        # Standard mode: capture audio and analyze
        from bird_listener.persistence.repository import SQLiteDetectionRepository
        from bird_listener.persistence.schema import init_db

        # Audio source
        if args.fake_audio:
            from bird_listener.audio.fake_capture import FakeAudioSource
            audio = FakeAudioSource()
        else:
            from bird_listener.audio.capture import MicrophoneAudioSource
            audio = MicrophoneAudioSource(
                duration_sec=config.capture_duration_sec,
                overlap_sec=config.capture_overlap_sec,
            )

        # Analyzer
        if args.analyzer == "birdnet-analyzer":
            from bird_listener.analysis.analyzer import BirdNetAnalyzer
            analyzer = BirdNetAnalyzer()
        else:
            from bird_listener.analysis.analyzer import BirdNetLibAnalyzer
            analyzer = BirdNetLibAnalyzer()

        # Database
        conn = init_db(config.db_path)
        repository = SQLiteDetectionRepository(conn)

        orchestrator = Orchestrator(
            config=config,
            repository=repository,
            renderer=renderer,
            display=display,
            audio=audio,
            analyzer=analyzer,
        )

        if args.once:
            orchestrator.run_once()
        else:
            orchestrator.run_loop()


if __name__ == "__main__":
    main()
