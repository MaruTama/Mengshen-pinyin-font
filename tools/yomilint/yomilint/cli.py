"""The command line: `yomilint check FONT... --spec yomilint.toml`."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import __version__
from .readers import DataError
from .report import as_json, as_text, summary
from .runner import run
from .spec import SpecError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yomilint",
        description="Check a font that annotates characters with their readings.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="run the checks on fonts")
    check.add_argument("fonts", nargs="+", metavar="FONT")
    check.add_argument("--spec", required=True, help="the spec file (yomilint.toml)")
    check.add_argument("--format", choices=["text", "json"], default="text")
    check.add_argument("--select", help="run only the checks whose id starts with this")
    check.add_argument(
        "--fail-on",
        choices=["error", "warn"],
        default="error",
        help="the least severity that makes the exit code 1 (default: error)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    failed = False
    for font in args.fonts:
        try:
            findings = run(font, args.spec, args.select)
        except (SpecError, DataError, OSError) as error:
            print(f"yomilint: {error}", file=sys.stderr)
            return 2
        print(as_json(font, findings) if args.format == "json" else as_text(font, findings))
        counts = summary(findings)
        failed = failed or counts["errors"] > 0
        if args.fail_on == "warn":
            failed = failed or counts["warnings"] > 0
    return 1 if failed else 0
