"""Entry point: GUI by default, CLI with --cli."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Random Password Generator")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the command-line version instead of the GUI.",
    )
    args = parser.parse_args()

    if args.cli:
        from cli import run_cli

        run_cli()
        return

    from app import run_gui

    run_gui()


if __name__ == "__main__":
    main()
