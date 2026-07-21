# -*- coding: utf-8 -*-
"""Glyph index and thumbnail SVGs for the glyph browser screen.

The index is built once per font selection from the TTFs via fonttools and
cached as tmp/projects/<id>/glyph_index.json; thumbnails are rendered on
demand with the same outline mechanism as the preview.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from src.refactored.scripts.retrieve_latin_alphabet import ALPHABET

from .. import settings
from ..schemas import Project
from .preview_composer import _FontOutlines
from .project_store import ProjectStore

INDEX_FILENAME = "glyph_index.json"
# Bump when index build logic changes so cached glyph_index.json regenerates
_INDEX_VERSION = "v5"

# The 55 latin letters (plain + tone-marked) actually used to compose
# pinyin. The pinyin category must stay within these — a full latin font
# carries hundreds of other letters that are not pinyin.
_PINYIN_ALPHABET = frozenset(ALPHABET)

_index_lock = threading.Lock()
_index_cache: Dict[str, tuple[str, List[dict]]] = {}
_standard_tables_cache: Optional[Dict[str, frozenset[int]]] = None

STANDARD_TABLE_LABELS = {
    "tgscc": "通用规范汉字表",
    "big5": "Big5 (2003)",
    "joyo": "常用漢字表",
}

# CJK blocks considered "hanzi" (incl. radicals, ext A/B+, compatibility)
_CJK_RANGES = (
    (0x2E80, 0x2FDF),
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
    (0x20000, 0x2FA1F),
)


def _is_cjk(codepoint: int) -> bool:
    return any(start <= codepoint <= end for start, end in _CJK_RANGES)


def standard_tables() -> Dict[str, frozenset[int]]:
    """Per-table codepoint sets parsed from res/download_unicode_tables/."""
    global _standard_tables_cache
    if _standard_tables_cache is not None:
        return _standard_tables_cache

    tables_dir = settings.PATHS.resources_dir / "download_unicode_tables"

    # TGSCC-Unicode.txt: "<index>\tU+XXXX"
    tgscc: set[int] = set()
    for line in _table_lines(tables_dir / "TGSCC-Unicode.txt"):
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith("U+"):
            tgscc.add(int(parts[1][2:], 16))

    # big5_2003-u2b.txt: "0xA1B1 0x00A7" (2nd column is Unicode; keep CJK only)
    big5: set[int] = set()
    for line in _table_lines(tables_dir / "big5_2003-u2b.txt"):
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith("0x"):
            codepoint = int(parts[1], 16)
            if _is_cjk(codepoint):
                big5.add(codepoint)

    # joyokanjihyo_20101130.txt: "04E00: 一"
    joyo: set[int] = set()
    for line in _table_lines(tables_dir / "joyokanjihyo_20101130.txt"):
        head = line.split(":", 1)[0].strip()
        if head and all(c in "0123456789ABCDEFabcdef" for c in head):
            joyo.add(int(head, 16))

    _standard_tables_cache = {
        "tgscc": frozenset(tgscc),
        "big5": frozenset(big5),
        "joyo": frozenset(joyo),
    }
    return _standard_tables_cache


def allowed_hanzi() -> frozenset[int]:
    """Union of 通用规范汉字表 (TGSCC), Big5 (2003), and 常用漢字表 (2010).

    The glyph browser only lists hanzi from these standard tables;
    everything else in the fonts' CJK blocks is noise for this UI.
    """
    tables = standard_tables()
    return tables["tgscc"] | tables["big5"] | tables["joyo"]


def tables_for(codepoints: List[int]) -> List[str]:
    """Which standard tables the glyph's codepoints belong to."""
    return [
        name
        for name, members in standard_tables().items()
        if any(cp in members for cp in codepoints)
    ]


def _table_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def _categorize(name: str, char: Optional[str]) -> str:
    if name.startswith("py_"):
        return "pinyin_alphabet"
    if char is not None and _is_cjk(ord(char)):
        return "hanzi"
    return "other"


def _built_output_path(project: Project) -> Optional[Path]:
    """Path of the built TTF, only when it reflects the current settings."""
    build = project.tasks.get("build")
    if build is None or build.status != "done":
        return None
    from .pipeline import output_path_for

    path = output_path_for(project)
    return path if path.exists() else None


def _pronunciation_entries(project: Project) -> List[dict]:
    """Generated pinyin-composed glyphs (<hanzi>.ssNN) from the built font.

    Pronunciation glyphs do not exist in the source fonts — the build
    composes them as .ss variants (ss00 = pinyin-less, ssNN = reading N).
    """
    from .preview_composer import get_pronunciations

    output_path = _built_output_path(project)
    if output_path is None:
        return []

    outlines = _FontOutlines(str(output_path), f"out:{output_path.stat().st_mtime}")
    reverse_cmap: Dict[str, List[int]] = {}
    for codepoint, glyph_name in outlines.cmap.items():
        reverse_cmap.setdefault(glyph_name, []).append(codepoint)

    allowed = allowed_hanzi()
    entries: List[dict] = []
    for glyph_name in outlines.font.getGlyphOrder():
        base_name, sep, variant = glyph_name.partition(".ss")
        if not sep or not variant.isdigit():
            continue
        codepoints = sorted(reverse_cmap.get(base_name, []))
        if not codepoints or not any(cp in allowed for cp in codepoints):
            continue
        char = chr(codepoints[0])
        index = int(variant)
        readings = get_pronunciations(project, char)
        homograph = len(readings) > 1
        if index == 0:
            reading = None
            label = f"{char}（拼音なし）"
            variant_label = "拼音なし"
        elif index <= len(readings):
            reading = readings[index - 1]
            label = f"{char}［{reading}］"
            variant_label = (
                f"第{index}読み: {reading}" if homograph else f"読み: {reading}"
            )
        else:
            continue  # stale variant beyond the current readings
        entries.append(
            {
                "name": glyph_name,
                "font": "output",
                "char": char,
                "label": label,
                "codepoints": [f"U+{cp:04X}" for cp in codepoints],
                "advance_width": outlines.advance_width(glyph_name),
                "category": "pronunciation",
                "variant": f"ss{variant}",
                "variant_label": variant_label,
                "reading": reading,
                "overridden": char in project.glyph_overrides.readings,
            }
        )
    return entries


def _build_index(project: Project) -> List[dict]:
    # Keyed by glyph name. Base and pinyin fonts often share latin glyph
    # names ("a", "amacron", ...); the pinyin font must own the pinyin
    # letters so they render in the pinyin typeface and are categorized
    # as pinyin_alphabet rather than being shadowed by the base font.
    by_name: Dict[str, dict] = {}
    allowed = allowed_hanzi()

    for role, font_ref in (
        ("base", project.base_font),
        ("pinyin", project.pinyin_font),
    ):
        if font_ref is None:
            continue
        outlines = _FontOutlines(font_ref.path, font_ref.sha256)
        reverse_cmap: Dict[str, List[int]] = {}
        for codepoint, glyph_name in outlines.cmap.items():
            reverse_cmap.setdefault(glyph_name, []).append(codepoint)

        for glyph_name in outlines.font.getGlyphOrder():
            codepoints = sorted(reverse_cmap.get(glyph_name, []))
            char = chr(codepoints[0]) if codepoints else None
            category = _categorize(glyph_name, char)
            # Hanzi are restricted to the standard tables
            # (通用规范汉字表 / Big5 / 常用漢字表)
            if category == "hanzi" and not any(cp in allowed for cp in codepoints):
                continue
            # The pinyin category is exactly the 55 letters used for pinyin,
            # not every latin/greek letter the font happens to carry
            is_pinyin_letter = role == "pinyin" and char in _PINYIN_ALPHABET
            if is_pinyin_letter and category == "other":
                category = "pinyin_alphabet"

            existing = by_name.get(glyph_name)
            if existing is not None:
                # Only the pinyin font's own pinyin letters may override an
                # already-seen (base-font) glyph of the same name
                if not (is_pinyin_letter and existing["category"] != "pinyin_alphabet"):
                    continue

            by_name[glyph_name] = {
                "name": glyph_name,
                "font": role,
                "char": char,
                "codepoints": [f"U+{cp:04X}" for cp in codepoints],
                "advance_width": outlines.advance_width(glyph_name),
                "category": category,
                "overridden": bool(char and char in project.glyph_overrides.readings),
            }

    entries = list(by_name.values())
    entries.extend(_pronunciation_entries(project))
    return entries


def _index_path(store: ProjectStore, project: Project) -> Path:
    return store.project_dir(project.id) / INDEX_FILENAME


def _fonts_key(project: Project) -> str:
    base = project.base_font.sha256 if project.base_font else "-"
    pinyin = project.pinyin_font.sha256 if project.pinyin_font else "-"
    overrides = ",".join(sorted(project.glyph_overrides.readings))
    output_path = _built_output_path(project)
    output = f"{output_path.stat().st_mtime}" if output_path else "-"
    return f"{_INDEX_VERSION}:{base}:{pinyin}:{overrides}:{output}"


def get_index(store: ProjectStore, project: Project) -> List[dict]:
    """Load (or build) the glyph index for the project."""
    key = _fonts_key(project)
    with _index_lock:
        cached = _index_cache.get(project.id)
        if cached is not None and cached[0] == key:
            return cached[1]

        index_path = _index_path(store, project)
        if index_path.exists():
            data = json.loads(index_path.read_text(encoding="utf-8"))
            if data.get("key") == key:
                _index_cache[project.id] = (key, data["glyphs"])
                return data["glyphs"]

        entries = _build_index(project)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps({"key": key, "glyphs": entries}, ensure_ascii=False),
            encoding="utf-8",
        )
        _index_cache[project.id] = (key, entries)
        return entries


def search(
    entries: List[dict],
    query: str = "",
    category: str = "",
    page: int = 1,
    size: int = 200,
) -> dict:
    filtered = entries
    if category:
        filtered = [e for e in filtered if e["category"] == category]
    if query:
        q = query.strip()
        q_upper = q.upper()
        if q_upper.startswith("U+"):
            filtered = [e for e in filtered if q_upper in e["codepoints"]]
        elif len(q) == 1 and not q.isascii():
            filtered = [e for e in filtered if e["char"] == q]
        else:
            q_lower = q.lower()
            filtered = [
                e for e in filtered if q_lower in e["name"].lower() or e["char"] == q
            ]

    total = len(filtered)
    start = max(page - 1, 0) * size
    return {
        "total": total,
        "page": page,
        "size": size,
        "glyphs": filtered[start : start + size],
    }


def find_glyph(entries: List[dict], name: str) -> Optional[dict]:
    for entry in entries:
        if entry["name"] == name:
            return entry
    return None


def ivs_sequences(readings: List[str]) -> List[dict]:
    """IVS selectors the build assigns to a hanzi with these readings.

    Mirrors FontBuilder._add_cmap_uvs: every hanzi with pinyin gets
    base+U+E01E0 -> ss00 (pinyin-less); homographs additionally get
    U+E01E0+i -> ss{i:02d} forcing reading i (GSUB bypassed).
    """
    from src.refactored.config.font_config import FontConstants

    if not readings:
        return []
    ivs_base = FontConstants.IVS_BASE
    sequences = [
        {
            "selector": f"U+{ivs_base:04X}",
            "glyph_suffix": "ss00",
            "reading": None,
            "description": "拼音なし",
        }
    ]
    if len(readings) > 1:
        for i, reading in enumerate(readings, start=1):
            sequences.append(
                {
                    "selector": f"U+{ivs_base + i:04X}",
                    "glyph_suffix": f"ss{i:02d}",
                    "reading": reading,
                    "description": "デフォルトの読み（強制）" if i == 1 else "異読",
                }
            )
    return sequences


def ivs_index(store: ProjectStore, project: Project) -> List[dict]:
    """Planned cmap_uvs rows for every hanzi in the project's base font."""
    from .preview_composer import get_pronunciations

    rows = []
    for entry in get_index(store, project):
        if entry["category"] != "hanzi" or entry["font"] != "base" or not entry["char"]:
            continue
        readings = get_pronunciations(project, entry["char"])
        if not readings:
            continue
        rows.append(
            {
                "char": entry["char"],
                "glyph": entry["name"],
                "readings": readings,
                "sequences": ivs_sequences(readings),
            }
        )
    return rows


def search_ivs(
    rows: List[dict],
    query: str = "",
    homographs_only: bool = False,
    page: int = 1,
    size: int = 50,
) -> dict:
    filtered = rows
    if homographs_only:
        filtered = [r for r in filtered if len(r["readings"]) > 1]
    if query:
        q = query.strip()
        filtered = [
            r
            for r in filtered
            if q == r["char"]
            or any(q in reading for reading in r["readings"])
            or q.upper() in {s["selector"] for s in r["sequences"]}
        ]
    total = len(filtered)
    start = max(page - 1, 0) * size
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": filtered[start : start + size],
    }


def thumbnail_svg(project: Project, entry: dict) -> Optional[str]:
    if entry["font"] == "output":
        output_path = _built_output_path(project)
        if output_path is None:
            return None
        outlines = _FontOutlines(str(output_path), f"out:{output_path.stat().st_mtime}")
        # Pinyin sits above the em square; the built font's raised
        # ascender covers it
        top = max(outlines.upem, float(outlines.font["hhea"].ascender))
    else:
        font_ref = project.base_font if entry["font"] == "base" else project.pinyin_font
        if font_ref is None:
            return None
        outlines = _FontOutlines(font_ref.path, font_ref.sha256)
        top = float(outlines.upem)
    try:
        path_d = outlines.svg_path(entry["name"])
    except KeyError:
        return None
    descent = abs(float(outlines.font["hhea"].descender))
    height = top + descent
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {entry["advance_width"]:.0f} {height:.0f}">'
        # Fixed fill: these render via <img>, where currentColor
        # would resolve to black and vanish on the dark background
        f'<g transform="translate(0 {top}) scale(1 -1)">'
        f'<path d="{path_d}" fill="#cbd5e1"/></g></svg>'
    )
