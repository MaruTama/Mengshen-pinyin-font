# -*- coding: utf-8 -*-
"""Bundled pinyin letter glyphs for the builtin pinyin (latin) fonts.

Some pinyin letters real readings need have no glyph in the builtin latin
fonts (e.g. ê̄ ê̌ m̄ m̀; the Seto subset also lacks ê ế ề). They are
composed once from the font's own glyphs (base letter + tone mark) and
shipped as reviewable data in res/fonts/custom_pinyin_glyphs/<style>.json:

    {
      "font": "<font file name>",
      "font_sha256": "<sha256 of the font file>",
      "glyphs": {
        "<ascii name, e.g. eh1>": {
          "letter": "<NFC pinyin letter>",
          "recipe": {...composition recipe...},
          "glyph": {"advanceWidth": n, "contours": [[{"x", "y", "on"}]]}
        }
      },
      "overrides": {...same entry format...}
    }

A bundle applies only to the exact font file it was composed from
(matched by sha256). ``glyphs`` only fill letters that font lacks;
``overrides`` (optional) replace letters the font does have but whose
shape does not suit pinyin (e.g. the double-story ``a`` -> single-story
``ɑ`` as taught in Chinese schools, issue #15).
Regenerate with: python tools/make_bundled_pinyin_glyphs.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

from ..config.paths import FONTS_DIR

BUNDLED_GLYPHS_DIR = FONTS_DIR / "custom_pinyin_glyphs"

Glyph = Dict[str, Any]
PathLike = Union[str, Path]


def file_sha256(path: PathLike) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_bundle_for_font(
    font_path: PathLike, bundle_dir: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """The bundle composed from this exact font file, if any."""
    directory = Path(bundle_dir) if bundle_dir is not None else BUNDLED_GLYPHS_DIR
    if not directory.is_dir() or not Path(font_path).is_file():
        return None
    sha = file_sha256(font_path)
    for bundle_path in sorted(directory.glob("*.json")):
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        if bundle.get("font_sha256") == sha:
            return bundle
    return None


def _section_for_font(
    font_path: PathLike, bundle_dir: Optional[Path], section: str
) -> Dict[str, Glyph]:
    bundle = load_bundle_for_font(font_path, bundle_dir)
    if bundle is None:
        return {}
    return {
        entry["letter"]: entry["glyph"] for entry in bundle.get(section, {}).values()
    }


def bundled_glyphs_for_font(
    font_path: PathLike, bundle_dir: Optional[Path] = None
) -> Dict[str, Glyph]:
    """Letter -> otfcc glyph filling letters the font lacks (or {})."""
    return _section_for_font(font_path, bundle_dir, "glyphs")


def bundled_overrides_for_font(
    font_path: PathLike, bundle_dir: Optional[Path] = None
) -> Dict[str, Glyph]:
    """Letter -> otfcc glyph replacing the font's own letter (or {})."""
    return _section_for_font(font_path, bundle_dir, "overrides")


def merge_bundled_glyphs(
    alphabet: Mapping[str, Glyph],
    bundled: Mapping[str, Glyph],
    overrides: Optional[Mapping[str, Glyph]] = None,
) -> Dict[str, Glyph]:
    """Add bundled letters the font lacks (the font's own glyphs win), then
    replace letters with their overrides."""
    merged = dict(alphabet)
    for letter, glyph in bundled.items():
        if letter not in merged:
            merged[letter] = glyph
    merged.update(overrides or {})
    return merged
