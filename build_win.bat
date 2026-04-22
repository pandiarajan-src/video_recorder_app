@echo off
:: Build recorder.exe and recorder-cli.exe into dist\recorder\
:: Run this on a Windows machine after: uv sync
uv run pyinstaller recorder.spec --clean
echo.
echo Build complete. Distribute the contents of dist\recorder\
