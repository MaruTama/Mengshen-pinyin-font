"""Known findings: a font with old problems can still fail on new ones.

A baseline file lists findings by check and subject. A run leaves them out
of its counts, and points out the ones that are no longer found, so the
file can be kept in step with the font.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Set, Tuple

from .checks import Finding
from .readers import DataError

Key = Tuple[str, str]


def key(finding: Finding) -> Key:
    return finding.check, finding.subject


def write_baseline(path: Path, findings: List[Finding]) -> None:
    known = [{"check": c, "subject": s} for c, s in sorted({key(f) for f in findings})]
    Path(path).write_text(
        json.dumps({"known": known}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_baseline(path: Path) -> Set[Key]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {(item["check"], item["subject"]) for item in data["known"]}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise DataError(f"cannot read the baseline {path}: {error}") from error


def split(
    findings: List[Finding], known: Set[Key], ran: Set[str]
) -> Tuple[List[Finding], List[Finding], List[Key]]:
    """The findings that are new, those that are known, and the known ones
    no longer found among the checks that ran."""
    new = [f for f in findings if key(f) not in known]
    old = [f for f in findings if key(f) in known]
    found = {key(f) for f in old}
    gone = sorted(k for k in known - found if k[0] in ran)
    return new, old, gone
