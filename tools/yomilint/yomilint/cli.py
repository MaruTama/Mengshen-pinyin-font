"""The command line: `yomilint check FONT... --spec yomilint.toml`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set

from . import __version__
from .baseline import Key, read_baseline, split, write_baseline
from .readers import DataError
from .report import as_json, as_text, summary
from .runner import run, selected
from .spec import SpecError, load_spec


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
        "--baseline",
        help="a file of known findings, which do not fail the run "
        "(default: [ignore] path of the spec)",
    )
    check.add_argument(
        "--fail-on",
        choices=["error", "warn"],
        default="error",
        help="the least severity that makes the exit code 1 (default: error)",
    )

    baseline = commands.add_parser(
        "baseline", help="save today's findings of a font as known"
    )
    baseline.add_argument("font", metavar="FONT")
    baseline.add_argument("--spec", required=True, help="the spec file (yomilint.toml)")
    baseline.add_argument("-o", "--output", required=True, help="the file to write")
    baseline.add_argument(
        "--select",
        help="save only the findings of the checks whose id starts with this",
    )
    return parser


def _check(args: argparse.Namespace) -> int:
    known: Set[Key] = set()
    path = args.baseline or load_spec(Path(args.spec)).baseline
    if path:
        known = read_baseline(Path(path))
    failed = False
    for font in args.fonts:
        findings = run(font, args.spec, args.select)
        new, old, gone = split(findings, known, selected(args.select))
        render = as_json if args.format == "json" else as_text
        print(render(font, new, len(old), gone))
        counts = summary(new)
        failed = failed or counts["errors"] > 0
        if args.fail_on == "warn":
            failed = failed or counts["warnings"] > 0
    return 1 if failed else 0


def _baseline(args: argparse.Namespace) -> int:
    findings = run(args.font, args.spec, args.select)
    write_baseline(Path(args.output), findings)
    print(f"{len({(f.check, f.subject) for f in findings})} findings saved as known")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _check(args) if args.command == "check" else _baseline(args)
    except (SpecError, DataError, OSError) as error:
        print(f"yomilint: {error}", file=sys.stderr)
        return 2
