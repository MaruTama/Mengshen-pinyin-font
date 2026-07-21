# -*- coding: utf-8 -*-
"""Name table construction for custom (uploaded) font builds.

Mirrors the entry shape of src/refactored/config/font_name_tables.py:
nameIDs 0-6, 13, 14 on platforms (1,0,0) and (3,1,1033). Copyright and
license strings are composed from both source fonts' own name entries so
the generated font carries its upstream attribution.
"""

from __future__ import annotations

from typing import Dict, List

from src.refactored.config.font_name_tables import VERSION, FontNameEntry

from ..schemas import LicenseInfo, Project
from .pipeline import sanitize_family_name

GENERATOR_CREDIT = (
    "Generated with Mengshen Pinyin Font tools "
    "(https://github.com/MaruTama/Mengshen-pinyin-font)"
)

_PLATFORMS = [
    {"platformID": 1, "encodingID": 0, "languageID": 0},
    {"platformID": 3, "encodingID": 1, "languageID": 1033},
]


def _entry_value(info: LicenseInfo, name_id: int) -> str:
    for entry in info.entries:
        if entry.name_id == name_id:
            return entry.value
    return ""


def _compose_multi(project: Project, name_id: int, fallback: str = "") -> str:
    """Join a name entry from both source fonts, dropping duplicates."""
    parts: List[str] = []
    for role in ("base", "pinyin"):
        info = project.license.get(role)
        if info:
            value = _entry_value(info, name_id)
            if value and value not in parts:
                parts.append(value)
    if not parts and fallback:
        parts.append(fallback)
    return "\n".join(parts)


def build_name_table(project: Project) -> List[Dict[str, object]]:
    family = sanitize_family_name(project.output.family_name)
    style = project.output.style_name or "Regular"
    full_name = f"{family}-{style}" if style != "Regular" else family

    copyright_text = _compose_multi(project, 0)
    copyright_text = (
        f"{copyright_text}\n{GENERATOR_CREDIT}" if copyright_text else GENERATOR_CREDIT
    )
    license_text = _compose_multi(
        project,
        13,
        fallback="See the license terms of the original fonts.",
    )
    license_url = _compose_multi(project, 14)

    name_values: List[tuple[int, str]] = [
        (0, copyright_text),
        (1, family),
        (2, style),
        (3, f"{VERSION};MENGSHEN;{full_name}"),
        (4, full_name),
        (5, f"Version {project.output.version or VERSION}"),
        (6, full_name),
        (13, license_text),
    ]
    if license_url:
        name_values.append((14, license_url))

    entries: List[FontNameEntry] = []
    for platform in _PLATFORMS:
        for name_id, value in name_values:
            entries.append(
                {
                    **platform,  # type: ignore[typeddict-item]
                    "nameID": name_id,
                    "nameString": value,
                }
            )
    return entries  # type: ignore[return-value]
