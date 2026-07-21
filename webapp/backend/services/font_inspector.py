# -*- coding: utf-8 -*-
"""Font metadata and license inspection via fonttools (no otfccdump)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Optional

from fontTools.ttLib import TTFont

from ..errors import FontValidationError
from ..schemas import FontRef, LicenseEntry

# nameID semantics follow src/refactored/config/font_name_tables.py
NAME_ID_LABELS = {
    0: "Copyright",
    1: "Font Family",
    2: "Subfamily",
    4: "Full Name",
    5: "Version",
    7: "Trademark",
    8: "Manufacturer",
    13: "License Description",
    14: "License URL",
}
LICENSE_NAME_IDS = [0, 1, 4, 5, 7, 8, 13, 14]


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _best_name(font: TTFont, name_id: int) -> Optional[str]:
    record = font["name"].getDebugName(name_id)
    return record


def read_license_entries(path: Path) -> List[LicenseEntry]:
    font = TTFont(str(path), lazy=True)
    try:
        entries = []
        for name_id in LICENSE_NAME_IDS:
            value = _best_name(font, name_id)
            if value:
                entries.append(
                    LicenseEntry(
                        name_id=name_id,
                        label=NAME_ID_LABELS.get(name_id, f"nameID {name_id}"),
                        value=value,
                    )
                )
        return entries
    finally:
        font.close()


def validate_font_file(path: Path) -> None:
    """Raise FontValidationError when the file is not a usable TTF/OTF."""
    try:
        font = TTFont(str(path), lazy=True)
    except Exception as e:  # noqa: BLE001 - fonttools raises many types
        raise FontValidationError("invalid_font", f"Not a valid font file: {e}") from e
    try:
        glyph_count = len(font.getGlyphOrder())
        if glyph_count >= 60000:
            raise FontValidationError(
                "glyph_count_exceeded",
                f"Font has {glyph_count} glyphs — too close to the 65,536 "
                "limit to add pinyin glyphs",
                count=glyph_count,
            )
        if "cmap" not in font or font.getBestCmap() is None:
            raise FontValidationError("no_cmap", "Font has no usable Unicode cmap")
    finally:
        font.close()


def pinyin_coverage(path: Path, alphabet: list[str]) -> list[str]:
    """Return alphabet characters missing from the font's cmap."""
    font = TTFont(str(path), lazy=True)
    try:
        cmap = font.getBestCmap()
        return [c for c in alphabet if ord(c) not in cmap]
    finally:
        font.close()


def normalize_pinyin_font(path: Path, alphabet: list[str]) -> Path:
    """Decompose composite alphabet glyphs into contours (TrueType only).

    retrieve_latin_alphabet copies glyphs verbatim; composite references
    would dangle in the generated alphabet JSON, breaking py_alphabet_*
    glyphs in the built font.
    """
    font = TTFont(str(path))
    try:
        if "glyf" not in font:
            return path  # CFF outlines have no composites to resolve

        from fontTools.pens.recordingPen import DecomposingRecordingPen
        from fontTools.pens.ttGlyphPen import TTGlyphPen

        glyf = font["glyf"]
        glyph_set = font.getGlyphSet()
        cmap = font.getBestCmap()
        changed = False
        for char in alphabet:
            glyph_name = cmap.get(ord(char))
            if glyph_name is None or not glyf[glyph_name].isComposite():
                continue
            recorder = DecomposingRecordingPen(glyph_set)
            glyph_set[glyph_name].draw(recorder)
            pen = TTGlyphPen(None)
            recorder.replay(pen)
            glyf[glyph_name] = pen.glyph()
            changed = True

        if not changed:
            return path

        normalized_path = path.with_name(f"{path.stem}_normalized{path.suffix}")
        font.save(str(normalized_path))
        return normalized_path
    finally:
        font.close()


def name_is_renderable(font: TTFont, text: str) -> bool:
    """True if the font has a glyph for every character in `text`.

    Pinyin alphabet fonts are lowercase-only latin subsets, so they can
    render their own family name (uppercase letters, hyphens) only partly;
    callers use this to avoid showing a name in a font that would fall
    back mid-word.
    """
    cmap = font.getBestCmap()
    return all(ord(ch) in cmap for ch in text)


def inspect_font(path: Path, source: str, original_filename: str) -> FontRef:
    font = TTFont(str(path), lazy=True)
    try:
        family = _best_name(font, 1) or _best_name(font, 4) or path.stem
        upem = int(font["head"].unitsPerEm)
        glyph_count = len(font.getGlyphOrder())
        name_renderable = name_is_renderable(font, family)
    finally:
        font.close()

    return FontRef(
        source=source,
        path=str(path),
        original_filename=original_filename,
        sha256=sha256_of(path),
        family_name=family,
        units_per_em=upem,
        glyph_count=glyph_count,
        name_renderable=name_renderable,
    )
