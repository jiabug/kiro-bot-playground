"""Entry point: python -m flakyscan <folder> [options]"""

import argparse
import sys
from datetime import date
from pathlib import Path

from .aggregator import aggregate
from .formatter import render
from .parser import parse_folder


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="flakyscan",
        description="Detect flaky tests from a folder of JUnit XML reports.",
    )
    p.add_argument(
        "folder",
        type=Path,
        help="Folder containing JUnit XML files from multiple CI runs.",
    )
    p.add_argument(
        "--min-runs",
        type=int,
        default=1,
        metavar="N",
        help="Skip tests seen fewer than N times total (default: 1).",
    )
    p.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: table (default) or json.",
    )
    p.add_argument(
        "--since",
        type=date.fromisoformat,
        default=None,
        metavar="YYYY-MM-DD",
        help="Only include reports with a testsuite timestamp >= this date.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    folder: Path = args.folder
    if not folder.exists():
        print(f"Error: folder not found: {folder}", file=sys.stderr)
        return 1
    if not folder.is_dir():
        print(f"Error: not a directory: {folder}", file=sys.stderr)
        return 1

    since: date | None = args.since

    runs = parse_folder(folder)
    stats = aggregate(runs, min_runs=args.min_runs, since=since)
    print(render(stats, fmt=args.format))
    return 0


if __name__ == "__main__":
    sys.exit(main())
