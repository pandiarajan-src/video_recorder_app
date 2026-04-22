# Video Recorder

A Windows screen recorder that saves to H.264 MP4. Supports a desktop GUI and a headless CLI for automation.

## Requirements

- Python 3.12+
- Windows (uses `mss` to capture the primary monitor)
- [uv](https://docs.astral.sh/uv/) package manager
- No external FFmpeg needed — `imageio-ffmpeg` bundles its own binary

## Installation

```bash
git clone <repo-url>
cd video_recorder_app
uv sync
```

## Configuration

Copy the example env file and edit as needed:

```bash
cp .env.example .env
```

`.env` contents:

```
DEFAULT_OUTPUT_DIR=~/Videos
```

## Usage

### Desktop GUI

```bash
uv run recorder
```

Start / Pause / Stop buttons control recording. Output directory is set from `.env` or chosen in the UI.

### Headless CLI

```bash
# Record for 30 seconds into a directory
uv run recorder-cli --output-dir ~/Videos --duration 30

# Custom FPS
uv run recorder-cli --output-dir ~/Videos --duration 60 --fps 15

# See all options
uv run recorder-cli --help
```

Segment file paths are printed to stdout on exit. Send `SIGINT` (Ctrl+C) or `SIGTERM` to stop early.

## Output

Files are named `recording_YYYYMMDD_HHMMSS_seg001.mp4`, `seg002.mp4`, etc. in the chosen directory. Each pause/resume cycle starts a new segment. Video is H.264 (`libx264`, CRF 23, ultrafast preset, `yuv420p`). No audio.

## Building a Redistributable EXE (Windows)

No Python required on the target machine.

```bat
:: On a Windows build machine:
uv sync
build_win.bat
```

Output is `dist\recorder\`. Zip that folder and distribute it.

- `recorder.exe` — desktop GUI (double-click to run)
- `recorder-cli.exe` — headless CLI

Users can place a `.env` file next to the EXE to override `DEFAULT_OUTPUT_DIR`. Without it, recordings go to `%USERPROFILE%\Videos`.

## Project Structure

```
src/recorder/
  capture.py   # Screen capture thread (mss → numpy RGB frames → queue)
  engine.py    # State machine: IDLE → RECORDING → PAUSED → IDLE
  ui.py        # tkinter GUI (calls engine only, no capture logic)
  cli.py       # Headless entry point
  main.py      # GUI entry point
```
