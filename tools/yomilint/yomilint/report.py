"""Findings as text for a person, or as JSON for a tool."""

from __future__ import annotations

import json
from collections import Counter
from typing import Dict, List

from .checks import CHECKS, ERROR, WARN, Finding

# A check that fails for every character would bury the rest.
SHOWN_PER_CHECK = 10


def summary(findings: List[Finding]) -> Dict[str, int]:
    counts = Counter(finding.severity for finding in findings)
    return {"errors": counts[ERROR], "warnings": counts[WARN]}


def as_text(font: str, findings: List[Finding]) -> str:
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
    counts = summary(findings)
    lines.append(f"  {counts['errors']} errors, {counts['warnings']} warnings")
    return "\n".join(lines)


def as_json(font: str, findings: List[Finding]) -> str:
    return json.dumps(
        {
            "font": font,
            "summary": summary(findings),
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
