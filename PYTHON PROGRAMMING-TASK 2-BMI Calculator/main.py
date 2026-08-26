"""BMI Calculator — GUI by default, CLI with --cli."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BMI Calculator")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the beginner command-line calculator instead of the GUI.",
    )
    args = parser.parse_args(argv)

    if args.cli:
        from cli import run_cli

        run_cli()
        return 0

    from gui import run_gui

    run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
