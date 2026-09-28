"""Entry point: `adrpy-tui [--path <repository>]`, or `--version`."""

import argparse
import sys
from importlib.metadata import PackageNotFoundError, metadata
from pathlib import Path

from adrpy_tui.core.versions import installed_version

_DOCS_URL = "https://github.com/FRACerqueira/adrpy-tui#readme"


def _print_version():
    try:
        summary = metadata("adrpy-tui")["Summary"]
    except PackageNotFoundError:
        summary = ""
    print(f"adrpy-tui {installed_version('adrpy-tui')}")
    print(f"adrpy-ai {installed_version('adrpy-ai')}")
    if summary:
        print(summary)
    print()
    print(f"Docs: {_DOCS_URL}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="adrpy-tui", description="Interactive terminal UI for adrpy.")
    parser.add_argument("--path", "-p", default=".", help="repository root directory (default: the current directory)")
    parser.add_argument("--version", "-v", action="store_true", help="show the installed versions and exit")
    args = parser.parse_args(argv)

    if args.version:
        _print_version()
        return 0
    repo = Path(args.path)
    if not repo.is_dir():
        parser.error(f"--path is not a directory: {args.path}")

    from adrpy_tui.ui.app import AdrpyTui

    AdrpyTui(repo).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
