"""Racing Coach application entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .config import load_config


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the FastAPI server."""
    import uvicorn
    from .api.app import create_app

    config = load_config(Path(args.config) if args.config else None)
    setup_logging(config.log_level)

    app = create_app(config)
    uvicorn.run(app, host=config.api.host, port=config.api.port)


def cmd_record(args: argparse.Namespace) -> None:
    """Record telemetry from a collector."""
    config = load_config(Path(args.config) if args.config else None)
    setup_logging(config.log_level)

    from .collectors.recorder import TelemetryRecorder
    from .storage.session_store import SessionStore
    from .storage.telemetry_store import TelemetryStore

    data_dir = config.data_dir
    session_store = SessionStore(data_dir / config.storage.db_name)
    telemetry_store = TelemetryStore(data_dir / config.storage.parquet_dir)

    # Select collector
    if config.collector.type == "mock":
        from .collectors.mock import MockCollector
        replay_file = Path(args.replay) if args.replay else None
        collector = MockCollector(
            sample_rate_hz=config.collector.sample_rate_hz,
            replay_file=replay_file,
        )
    elif config.collector.type == "ac":
        from .collectors.ac_shared_memory import ACSharedMemoryCollector
        collector = ACSharedMemoryCollector(
            sample_rate_hz=config.collector.sample_rate_hz,
        )
    else:
        print(f"Unknown collector type: {config.collector.type}", file=sys.stderr)
        sys.exit(1)

    recorder = TelemetryRecorder(
        collector=collector,
        session_store=session_store,
        telemetry_store=telemetry_store,
        buffer_size=config.collector.buffer_size,
    )

    async def run():
        async with collector:
            await recorder.run(
                track=args.track or "unknown",
                car=args.car or "unknown",
            )

    asyncio.run(run())


def cmd_import_ld(args: argparse.Namespace) -> None:
    """Import MoTeC .ld telemetry files."""
    config = load_config(Path(args.config) if args.config else None)
    setup_logging(config.log_level)

    from .importer import import_ld_file
    from .storage.session_store import SessionStore
    from .storage.telemetry_store import TelemetryStore

    data_dir = config.data_dir
    session_store = SessionStore(data_dir / config.storage.db_name)
    telemetry_store = TelemetryStore(data_dir / config.storage.parquet_dir)

    for ld_path in args.files:
        p = Path(ld_path)
        if not p.exists():
            print(f"File not found: {p}", file=sys.stderr)
            continue
        try:
            sid = import_ld_file(p, session_store, telemetry_store)
            session = session_store.get_session(sid)
            laps = session_store.get_laps(sid)
            best = min((l.lap_time_ms for l in laps), default=0)
            best_str = f"{best/1000:.3f}s" if best else "-"
            print(f"  {p.name} → session {sid} | {session.track} / {session.car} | "
                  f"{len(laps)} laps | best {best_str}")
        except Exception as e:
            print(f"  ERROR importing {p.name}: {e}", file=sys.stderr)

    session_store.close()


def cmd_generate_mock(args: argparse.Namespace) -> None:
    """Generate mock telemetry data for development."""
    config = load_config(Path(args.config) if args.config else None)
    setup_logging(config.log_level)

    from .collectors.mock import MockCollector
    from .collectors.recorder import TelemetryRecorder
    from .storage.session_store import SessionStore
    from .storage.telemetry_store import TelemetryStore

    data_dir = config.data_dir
    session_store = SessionStore(data_dir / config.storage.db_name)
    telemetry_store = TelemetryStore(data_dir / config.storage.parquet_dir)

    collector = MockCollector(
        sample_rate_hz=args.rate,
        num_laps=args.laps,
    )

    recorder = TelemetryRecorder(
        collector=collector,
        session_store=session_store,
        telemetry_store=telemetry_store,
    )

    async def run():
        async with collector:
            await recorder.run(
                track=args.track,
                car=args.car,
            )

    print(f"Generating {args.laps} laps of mock data...")
    asyncio.run(run())
    print("Done! Start the server with: racing-coach serve")


def main() -> None:
    parser = argparse.ArgumentParser(description="Racing Coach - Telemetry Analysis & AI Coaching")
    parser.add_argument("--config", help="Path to config TOML file")
    sub = parser.add_subparsers(dest="command")

    # serve
    serve_p = sub.add_parser("serve", help="Start the web server")

    # record
    record_p = sub.add_parser("record", help="Record telemetry")
    record_p.add_argument("--track", default="unknown")
    record_p.add_argument("--car", default="unknown")
    record_p.add_argument("--replay", help="Parquet file to replay")

    # generate-mock
    mock_p = sub.add_parser("generate-mock", help="Generate mock telemetry data")
    mock_p.add_argument("--laps", type=int, default=5)
    mock_p.add_argument("--rate", type=int, default=50, help="Sample rate Hz")
    mock_p.add_argument("--track", default="Monza")
    mock_p.add_argument("--car", default="Ferrari 488 GT3")

    # import-ld
    import_p = sub.add_parser("import-ld", help="Import MoTeC .ld telemetry files")
    import_p.add_argument("files", nargs="+", help="One or more .ld files")

    args = parser.parse_args()

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "record":
        cmd_record(args)
    elif args.command == "import-ld":
        cmd_import_ld(args)
    elif args.command == "generate-mock":
        cmd_generate_mock(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
