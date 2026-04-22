"""Screen capture layer using mss. Swap this file to change capture backend."""

import time
import queue
import threading
import numpy as np
import mss


class ScreenCapture:
    """Grabs frames at target FPS and pushes numpy arrays into a queue."""

    def __init__(self, frame_queue: queue.Queue, fps: int = 15):
        self._queue = frame_queue
        self._fps = fps
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def _capture_loop(self) -> None:
        interval = 1.0 / self._fps
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            while not self._stop_event.is_set():
                t0 = time.monotonic()
                frame = np.array(sct.grab(monitor))
                # mss returns BGRA; drop alpha → BGR for imageio-ffmpeg (expects RGB)
                frame = frame[:, :, :3][:, :, ::-1]  # BGRA→BGR→RGB
                try:
                    self._queue.put_nowait(frame)
                except queue.Full:
                    pass  # drop frame rather than block
                elapsed = time.monotonic() - t0
                sleep = interval - elapsed
                if sleep > 0:
                    time.sleep(sleep)
