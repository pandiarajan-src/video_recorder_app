"""RecorderEngine: state machine + thread coordination + segment file management."""

import queue
import threading
from datetime import datetime
from enum import Enum, auto
from pathlib import Path

import imageio_ffmpeg

from .capture import ScreenCapture


class State(Enum):
    IDLE = auto()
    RECORDING = auto()
    PAUSED = auto()


class RecorderEngine:
    """
    Controls the recording lifecycle.

    State transitions:
        IDLE → start() → RECORDING
        RECORDING → pause() → PAUSED
        RECORDING → stop() → IDLE
        PAUSED → resume() → RECORDING
        PAUSED → stop() → IDLE
    """

    QUEUE_SIZE = 30

    def __init__(self, fps: int = 15) -> None:
        self._fps = fps
        self._state = State.IDLE
        self._segments: list[Path] = []
        self._session_prefix: str = ""
        self._output_dir: Path = Path.home() / "Videos"

        self._frame_queue: queue.Queue = queue.Queue(maxsize=self.QUEUE_SIZE)
        self._capture = ScreenCapture(self._frame_queue, fps=self._fps)

        self._encode_stop = threading.Event()
        self._encode_thread: threading.Thread | None = None
        self._writer = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def state(self) -> State:
        return self._state

    @property
    def segments(self) -> list[Path]:
        return list(self._segments)

    def start(self, output_dir: Path) -> None:
        if self._state != State.IDLE:
            return
        self._output_dir = output_dir
        self._segments = []
        self._session_prefix = datetime.now().strftime("recording_%Y%m%d_%H%M%S")
        self._state = State.RECORDING
        self._start_segment()

    def pause(self) -> None:
        if self._state != State.RECORDING:
            return
        self._state = State.PAUSED
        self._stop_segment()

    def resume(self) -> None:
        if self._state != State.PAUSED:
            return
        self._state = State.RECORDING
        self._start_segment()

    def stop(self) -> list[Path]:
        if self._state == State.IDLE:
            return []
        if self._state == State.RECORDING:
            self._stop_segment()
        self._state = State.IDLE
        return self.segments

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_segment_path(self) -> Path:
        seg_num = len(self._segments) + 1
        name = f"{self._session_prefix}_seg{seg_num:03d}.mp4"
        return self._output_dir / name

    def _start_segment(self) -> None:
        seg_path = self._next_segment_path()
        self._segments.append(seg_path)
        self._encode_stop.clear()
        # drain stale frames before starting fresh
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break
        self._capture.start()
        self._encode_thread = threading.Thread(
            target=self._encode_loop, args=(seg_path,), daemon=True
        )
        self._encode_thread.start()

    def _stop_segment(self) -> None:
        self._capture.stop()
        self._encode_stop.set()
        if self._encode_thread:
            self._encode_thread.join(timeout=10)
            self._encode_thread = None

    def _encode_loop(self, seg_path: Path) -> None:
        writer = None
        try:
            while not self._encode_stop.is_set() or not self._frame_queue.empty():
                try:
                    frame = self._frame_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if writer is None:
                    h, w = frame.shape[:2]
                    writer = imageio_ffmpeg.write_frames(
                        str(seg_path),
                        size=(w, h),
                        fps=self._fps,
                        codec="libx264",
                        output_params=["-crf", "23", "-preset", "ultrafast", "-pix_fmt", "yuv420p"],
                    )
                    writer.send(None)  # prime the generator
                writer.send(frame.tobytes())
        finally:
            if writer is not None:
                try:
                    writer.close()
                except StopIteration:
                    pass
