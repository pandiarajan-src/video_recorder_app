# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the Windows screen recorder.

Builds two EXEs into dist/recorder/:
  recorder.exe      – windowed GUI (no console window)
  recorder-cli.exe  – headless CLI (console)

Run on a Windows machine:
  uv run pyinstaller recorder.spec

Output: dist/recorder/  (zip this folder to redistribute)
"""

from PyInstaller.utils.hooks import collect_data_files

# imageio-ffmpeg ships a bundled ffmpeg.exe inside its package;
# collect_data_files picks up the binaries/ sub-directory correctly.
_imageio_datas = collect_data_files("imageio_ffmpeg")

a = Analysis(
    ["run_gui.py", "run_cli.py"],
    pathex=["src"],
    binaries=[],
    datas=_imageio_datas,
    # mss.windows is loaded dynamically on Windows; list it explicitly.
    hiddenimports=["mss", "mss.windows"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

# --- GUI entry point (no console window) ---
exe_gui = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="recorder",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    argv_emulation=False,
)

# --- CLI entry point (console window) ---
exe_cli = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="recorder-cli",
    debug=False,
    strip=False,
    upx=True,
    console=True,
    argv_emulation=False,
)

# Collect both EXEs plus all shared binaries/data into one folder.
coll = COLLECT(
    exe_gui,
    exe_cli,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="recorder",
)
