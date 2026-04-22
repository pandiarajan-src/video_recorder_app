"""RecorderDialog: tkinter UI. Calls RecorderEngine; never contains business logic."""

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from dotenv import load_dotenv

from .engine import RecorderEngine, State

load_dotenv()


class RecorderDialog:
    _BTN_WIDTH = 10
    _PAD = 8

    def __init__(self) -> None:
        self._engine = RecorderEngine()
        self._root = tk.Tk()
        self._root.title("Screen Recorder")
        self._root.resizable(False, False)
        self._output_dir = tk.StringVar(
            value=os.getenv("DEFAULT_OUTPUT_DIR", str(Path.home() / "Videos"))
        )
        self._status_text = tk.StringVar(value="Idle")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = self._root
        pad = self._PAD

        # Output directory row
        dir_frame = tk.Frame(root)
        dir_frame.pack(fill=tk.X, padx=pad, pady=(pad, 0))
        tk.Label(dir_frame, text="Save to:").pack(side=tk.LEFT)
        tk.Entry(dir_frame, textvariable=self._output_dir, width=32).pack(
            side=tk.LEFT, padx=(4, 4)
        )
        tk.Button(dir_frame, text="Browse", command=self._browse).pack(side=tk.LEFT)

        # Button row
        btn_frame = tk.Frame(root)
        btn_frame.pack(padx=pad, pady=pad)

        self._btn_start = tk.Button(
            btn_frame, text="Start", width=self._BTN_WIDTH, command=self._on_start
        )
        self._btn_pause = tk.Button(
            btn_frame, text="Pause", width=self._BTN_WIDTH, command=self._on_pause, state=tk.DISABLED
        )
        self._btn_resume = tk.Button(
            btn_frame, text="Resume", width=self._BTN_WIDTH, command=self._on_resume, state=tk.DISABLED
        )
        self._btn_stop = tk.Button(
            btn_frame, text="Stop", width=self._BTN_WIDTH, command=self._on_stop, state=tk.DISABLED
        )

        for btn in (self._btn_start, self._btn_pause, self._btn_resume, self._btn_stop):
            btn.pack(side=tk.LEFT, padx=3)

        # Status bar
        tk.Label(root, textvariable=self._status_text, relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, padx=pad, pady=(0, pad)
        )

        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _browse(self) -> None:
        path = filedialog.askdirectory(initialdir=self._output_dir.get())
        if path:
            self._output_dir.set(path)

    def _on_start(self) -> None:
        output_dir = Path(self._output_dir.get())
        if not output_dir.is_dir():
            messagebox.showerror("Invalid directory", f"Directory not found:\n{output_dir}")
            return
        self._engine.start(output_dir)
        self._sync_buttons()
        self._status_text.set("Recording...")

    def _on_pause(self) -> None:
        self._engine.pause()
        self._sync_buttons()
        self._status_text.set(f"Paused  (segments so far: {len(self._engine.segments)})")

    def _on_resume(self) -> None:
        self._engine.resume()
        self._sync_buttons()
        self._status_text.set("Recording...")

    def _on_stop(self) -> None:
        segments = self._engine.stop()
        self._sync_buttons()
        names = "\n".join(p.name for p in segments)
        self._status_text.set(f"Stopped  ({len(segments)} segment(s) saved)")
        messagebox.showinfo("Recording stopped", f"Saved {len(segments)} segment(s):\n{names}")

    def _on_close(self) -> None:
        if self._engine.state != State.IDLE:
            self._engine.stop()
        self._root.destroy()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sync_buttons(self) -> None:
        state = self._engine.state
        self._btn_start.config(state=tk.NORMAL if state == State.IDLE else tk.DISABLED)
        self._btn_pause.config(state=tk.NORMAL if state == State.RECORDING else tk.DISABLED)
        self._btn_resume.config(state=tk.NORMAL if state == State.PAUSED else tk.DISABLED)
        self._btn_stop.config(state=tk.DISABLED if state == State.IDLE else tk.NORMAL)

    def run(self) -> None:
        self._root.mainloop()
