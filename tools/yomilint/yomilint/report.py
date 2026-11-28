"""Findings as text for a person, or as JSON for a tool."""

from __future__ import annotations

import json
from collections import Counter
from typing import Dict, List, Sequence, Tuple

from .checks import CHECKS, ERROR, WARN, Finding

# A check that fails for every character would bury the rest.
SHOWN_PER_CHECK = 10


def summary(findings: List[Finding]) -> Dict[str, int]:
    counts = Counter(finding.severity for finding in findings)
    return {"errors": counts[ERROR], "warnings": counts[WARN]}


def as_text(
    font: str,
    findings: List[Finding],
    known: int = 0,
    gone: Sequence[Tuple[str, str]] = (),
) -> str:
    lines = [font]
    by_check: Dict[str, List[Finding]] = {}
    for finding in findings:
        by_check.setdefault(finding.check, []).append(finding)
    rationale = {check.id: check.rationale for check in CHECKS}
    for check_id, found in by_check.items():
        lines.append(f"  {found[0].severity} {check_id} ({len(found)})")
        lines.append(f"    {rationale.get(check_id, '')}")
        for finding in found[:SHOWN_PER_CHECK]:
            lines.append(f"    - {finding.subject}: {finding.message}")
        if len(found) > SHOWN_PER_CHECK:
            lines.append(f"    ... and {len(found) - SHOWN_PER_CHECK} more")
    for check_id, subject in gone:
        lines.append(f"  known but no longer found: {check_id} {subject}")
    counts = summary(findings)
    total = f"  {counts['errors']} errors, {counts['warnings']} warnings"
    if known or gone:
        total += f", {known} known"
    lines.append(total)
    return "\n".join(lines)


def as_json(
    font: str,
    findings: List[Finding],
    known: int = 0,
    gone: Sequence[Tuple[str, str]] = (),
) -> str:
    return json.dumps(
        {
            "font": font,
            "summary": {**summary(findings), "known": known},
            "no_longer_found": [
                {"check": check_id, "subject": subject} for check_id, subject in gone
            ],
            "findings": [
                {
                    "check": finding.check,
                    "severity": finding.severity,
                    "subject": finding.subject,
                    "message": finding.message,
                }
                for finding in findings
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
