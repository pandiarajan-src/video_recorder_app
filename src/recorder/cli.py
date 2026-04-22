"""
Headless CLI recorder for automation use.

Usage:
    uv run recorder-cli --output-dir C:\\Videos --duration 30
    uv run recorder-cli --output-dir C:\\Videos          # runs until Ctrl+C / SIGTERM
"""

import argparse
import os
import signal
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv

from .engine import RecorderEngine

load_dotenv()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="recorder-cli",
        description="Record the screen to MP4 segments without a GUI.",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=os.getenv("DEFAULT_OUTPUT_DIR", str(Path.home() / "Videos")),
        help="Directory to save recordings (default: %(default)s)",
    )
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Stop automatically after this many seconds. 0 = run until Ctrl+C (default: 0)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=15,
        help="Capture frame rate (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not output_dir.is_dir():
        print(f"ERROR: output directory not found: {output_dir}", file=sys.stderr)
        sys.exit(1)

    engine = RecorderEngine(fps=args.fps)
    stop_event = threading.Event()

    def _handle_stop(signum=None, frame=None) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_stop)

    engine.start(output_dir)
    print(f"Recording started  output={output_dir}  fps={args.fps}", flush=True)

    if args.duration > 0:
        print(f"Duration: {args.duration}s", flush=True)
        stop_event.wait(timeout=args.duration)
    else:
        print("Running until Ctrl+C or SIGTERM.", flush=True)
        stop_event.wait()

    segments = engine.stop()
    print(f"Recording stopped  segments={len(segments)}", flush=True)
    for seg in segments:
        print(str(seg), flush=True)


if __name__ == "__main__":
    main()
