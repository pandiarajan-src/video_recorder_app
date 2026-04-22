"""Entry point: uv run python -m recorder"""

from .ui import RecorderDialog


def main() -> None:
    RecorderDialog().run()


if __name__ == "__main__":
    main()
