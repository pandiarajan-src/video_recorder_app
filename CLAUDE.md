# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install / sync dependencies
uv sync

# Verify all modules import cleanly (quick smoke test)
uv run python -c "from recorder.engine import RecorderEngine; from recorder.cli import main; print('OK')"

# Run the desktop GUI (Windows only)
uv run recorder

# Run the headless CLI
uv run recorder-cli --output-dir <dir> --duration <seconds>
uv run recorder-cli --help

# Run as a module
uv run python -m recorder        # GUI
uv run python -m recorder.cli    # CLI

# Add a dependency
uv add <package>
```

## Architecture

The package lives in `src/recorder/`. Three layers with strict separation:

| File | Role |
|------|------|
| `capture.py` | Capture-only layer — wraps `mss`, runs on its own thread, pushes `numpy` RGB frames into a bounded `queue.Queue`. Swap this file to change the capture backend (e.g. dxcam). |
| `engine.py` | Business logic — `RecorderEngine` is a state machine (`IDLE → RECORDING → PAUSED → IDLE`). Owns the capture thread, the encode thread, and all segment file paths. Never imports UI code. |
| `ui.py` | `RecorderDialog` (tkinter) — pure UI. Calls engine methods only; reads `engine.state` to enable/disable buttons. |
| `cli.py` | Headless entry point for automation. Thin wrapper around `RecorderEngine`: parses `--output-dir / --duration / --fps`, installs `SIGINT`/`SIGTERM` handlers, prints segment paths to stdout on exit. |
| `main.py` | GUI entry point — instantiates `RecorderDialog` and calls `.run()`. |

### Pause/resume = multiple segment files

True stream pause is not implemented. Each `pause()` closes the current MP4; each `resume()` opens a new one. Segments are named `recording_YYYYMMDD_HHMMSS_seg001.mp4`, `seg002.mp4`, etc. in the chosen output directory.

### Threading model

- **Main thread** — tkinter event loop (GUI) or `threading.Event.wait()` (CLI)  
- **Capture thread** — `ScreenCapture._capture_loop` runs inside `mss.mss()` context, targets the configured FPS  
- **Encode thread** — `RecorderEngine._encode_loop` drains the frame queue and writes via `imageio_ffmpeg.write_frames` (generator API: `send(None)` to prime, `send(bytes)` per frame, `.close()` to finalise)

Queue is bounded (`maxsize=30`); frames are dropped rather than blocking the capture thread.

## Configuration

`.env` in the project root is loaded by both `ui.py` and `cli.py`:

```
DEFAULT_OUTPUT_DIR=~/Videos
```

## Key constraints

- **Windows target** — `mss` captures the primary monitor (`monitors[1]`). No multi-monitor selection yet.
- **No audio** — video-only recording.
- Output is H.264 MP4 (`libx264`, CRF 23, ultrafast preset, `yuv420p`).
- `imageio-ffmpeg` bundles its own FFmpeg binary — no external FFmpeg installation required on the target machine.

## Gotchas

- **Frame colour order**: `mss` returns BGRA; `capture.py` converts to RGB (`[:, :, :3][:, :, ::-1]`) before queuing. `imageio-ffmpeg` expects RGB — don't skip this step if rewriting the capture layer.
- **Queue drain on resume**: `_start_segment` flushes the frame queue before starting a new segment to avoid stale frames leaking into the next MP4.
- **Build backend**: `hatchling` is used (`[build-system]` in `pyproject.toml`). The wheel includes only `src/recorder/`; adding a new sub-package requires updating `[tool.hatch.build.targets.wheel]`.
