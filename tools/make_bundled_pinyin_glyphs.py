# -*- coding: utf-8 -*-
"""Regenerate res/fonts/custom_pinyin_glyphs/<style>.json.

Composes the pinyin letters each builtin pinyin (latin) font lacks from
the font's own glyphs (base letter + the tone mark of an accented letter),
using the webapp's composer, and writes recipe + resulting otfcc glyph as
reviewable data. The core pipeline merges them into the alphabet JSON
(retrieve_latin_alphabet) only for letters the font lacks. Letters the
font has but whose shape is replaced for pinyin (STYLE_OVERRIDES, e.g.
single-story a) go to the bundle's "overrides" section.

Usage (from the repository root):
    python tools/make_bundled_pinyin_glyphs.py [--style han_serif|handwritten]
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.refactored.config.font_config import FontConfig, FontType  # noqa: E402
from src.refactored.utils.bundled_glyphs import (  # noqa: E402
    BUNDLED_GLYPHS_DIR,
    file_sha256,
)
from src.refactored.utils.pinyin_utils import PINYIN_TONE_TO_NUMERIC  # noqa: E402
from webapp.backend.services import glyph_composer  # noqa: E402
from webapp.backend.services.custom_glyphs import (  # noqa: E402
    DEFAULT_RECIPES,
    font_glyph,
)
from webapp.backend.services.preview_composer import _FontOutlines  # noqa: E402

# Per-style letters to bundle, in composition order (ê before ê̄ etc.),
# with recipe tweaks over the webapp defaults (custom_glyphs.DEFAULT_RECIPES).
# Offsets are in font units of the respective pinyin font.
STYLE_RECIPES: Dict[str, List[Dict[str, Any]]] = {
    # mplus-1m-medium (upem 1000): has ê ế ề ḿ ń ň ǹ. Its own ǚ/ế top out
    # at 895/875; ê̄/ê̌ stack a reduced mark just above the circumflex.
    "han_serif": [
        {"letter": "ê̄", "scale": 0.9, "gap": 35},  # ê̄
        {"letter": "ê̌", "scale": 0.6, "gap": 35},  # ê̌
        {"letter": "m̄"},  # m̄
        {"letter": "m̀"},  # m̀
    ],
    # latin-alphabet-of-SetoFont-SP (upem 1024): has ḿ ń ň ǹ only (ǚ tops
    # out at 692). ế/ề put a small acute/grave to the right of the
    # circumflex like mplus does; ê̄/ê̌ stack a reduced mark above it.
    "handwritten": [
        {"letter": "ê", "scale": 0.9},  # ê (mirrored caron of ě)
        {"letter": "ê̄", "scale": 0.8, "gap": 35},  # ê̄
        {"letter": "ế", "scale": 0.7, "dx": 150, "gap": -70},  # ế
        {"letter": "ê̌", "scale": 0.6, "gap": 35},  # ê̌
        {"letter": "ề", "scale": 0.7, "dx": 170, "gap": -50},  # ề
        {"letter": "m̄"},  # m̄
        {"letter": "m̀"},  # m̀
    ],
}


# Per-style letters the font has but whose shape is replaced for pinyin
# (bundle "overrides"). Issue #15: pinyin a is the single-story ɑ, as
# taught in Chinese schools, consistently for a ā á ǎ à. Entry kinds:
#   {"letter", "base"}                 -> copy of the base glyph
#   {"letter", "base", "mark_source"}  -> base + tone mark (like STYLE_RECIPES;
#                                         "gap" supported). The base may be
#                                         an earlier override (e.g. "a").
#   {"letter", "strip_mark_of"}        -> that glyph minus its tone mark
#                                         (optional "mark_contours")
# Mark sources and the plain letters used for mark detection are always
# the font's own glyphs.
STYLE_OVERRIDES: Dict[str, List[Dict[str, Any]]] = {
    # mplus: a/ā/á/ǎ/à are double-story; its own ɑ (U+0251) gets the
    # unchanged tone marks of ā/á/ǎ/à, re-centered over it (keeping each
    # mark's designed offset from the body center and its height).
    "han_serif": [
        {"letter": "a", "base": "ɑ"},
        {"letter": "ā", "base": "ɑ", "mark_source": "ā"},
        {"letter": "á", "base": "ɑ", "mark_source": "á"},
        {"letter": "ǎ", "base": "ɑ", "mark_source": "ǎ"},
        {"letter": "à", "base": "ɑ", "mark_source": "à"},
    ],
    # Seto has no ɑ and its only single-story a is the body of ǎ (a, á,
    # à are double-story, ā has a descending tail). a = ǎ minus its caron;
    # ā/á/à = that body + their own marks, placed 61 units above it like
    # ǎ's caron (caron bottom 504 - body top 443). ǎ stays the font's.
    "handwritten": [
        # caron = contour 2 (it dips below a's top: not auto-detected)
        {"letter": "a", "strip_mark_of": "ǎ", "mark_contours": [2]},
        {"letter": "ā", "base": "a", "mark_source": "ā", "gap": 61},
        {"letter": "á", "base": "a", "mark_source": "á", "gap": 61},
        {"letter": "à", "base": "a", "mark_source": "à", "gap": 61},
    ],
}


def recipe_for(entry: Dict[str, Any]) -> Dict[str, Any]:
    base, mark_source, flip_y = DEFAULT_RECIPES.get(
        entry["letter"], (entry.get("base"), entry.get("mark_source"), False)
    )
    return {
        "base": entry.get("base", base),
        "mark_source": entry.get("mark_source", mark_source),
        "mark_contours": entry.get("mark_contours"),
        "dx": float(entry.get("dx", 0.0)),
        "dy": float(entry.get("dy", 0.0)),
        "scale": float(entry.get("scale", 1.0)),
        "flip_y": bool(entry.get("flip_y", flip_y)),
    }


Lookup = Callable[[str], Optional[Dict[str, Any]]]


def _compose_entry(
    style: str,
    entry: Dict[str, Any],
    lookup: Lookup,
    base_lookup: Optional[Lookup] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """(recipe, glyph) of base + tone mark per a recipe entry.

    The base comes from ``base_lookup`` (default ``lookup``); the mark
    source and its plain letter (for mark detection) from ``lookup``.
    """
    letter = entry["letter"]
    recipe = recipe_for(entry)
    base = (base_lookup or lookup)(recipe["base"])
    source = lookup(recipe["mark_source"])
    if base is None or source is None:
        raise SystemExit(f"{style}: missing base/mark glyph for {letter}")
    plain_letter = unicodedata.normalize("NFD", recipe["mark_source"])[:1]

    def compose(recipe: Dict[str, Any]) -> glyph_composer.Composition:
        return glyph_composer.compose(
            base,
            source,
            lookup(plain_letter),
            glyph_composer.Recipe(
                dx=recipe["dx"],
                dy=recipe["dy"],
                scale=recipe["scale"],
                flip_y=recipe["flip_y"],
                mark_contours=recipe["mark_contours"],
            ),
        )

    result = compose(recipe)
    # "gap": put the (scaled) mark's bottom exactly `gap` units above
    # the base's top, so stacked marks stay compact (pinyin is scaled
    # into a fixed canvas) without touching the circumflex. The
    # resulting dy is what gets recorded in the recipe.
    if "gap" in entry:
        base_box = glyph_composer.bbox(base["contours"])
        mark_box = glyph_composer.bbox(
            result.glyph["contours"][result.base_contour_count :]
        )
        if base_box and mark_box:
            recipe["dy"] += base_box[3] + entry["gap"] - mark_box[1]
            result = compose(recipe)
    return recipe, result.glyph


def _override_entry(
    style: str, entry: Dict[str, Any], font_lookup: Lookup, base_lookup: Lookup
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """(recipe, glyph) for a STYLE_OVERRIDES entry.

    Bases resolve via ``base_lookup`` (earlier overrides first); mark
    sources and plain letters via ``font_lookup``.
    """
    letter = entry["letter"]
    if "strip_mark_of" in entry:
        source_letter = entry["strip_mark_of"]
        source = font_lookup(source_letter)
        if source is None:
            raise SystemExit(f"{style}: missing glyph {source_letter} for {letter}")
        plain = font_lookup(unicodedata.normalize("NFD", source_letter)[:1])
        indices = entry.get("mark_contours") or glyph_composer.detect_mark_contours(
            source, plain
        )
        glyph = glyph_composer.strip_mark(source, plain, indices or None)
        return {"strip_mark_of": source_letter, "mark_contours": indices}, glyph
    if "mark_source" in entry:
        return _compose_entry(style, entry, font_lookup, base_lookup)
    base = base_lookup(entry["base"])
    if base is None:
        raise SystemExit(f"{style}: missing glyph {entry['base']} for {letter}")
    return {"base": entry["base"]}, base


def build_bundle(style: str) -> Dict[str, Any]:
    font_path = FontConfig.get_alphabet_font_path(FontType(style))
    outlines = _FontOutlines(str(font_path), "bundle")
    composed: Dict[str, Dict[str, Any]] = {}

    def font_lookup(letter: str) -> Optional[Dict[str, Any]]:
        return font_glyph(outlines, letter)

    def lookup(letter: str) -> Optional[Dict[str, Any]]:
        return font_lookup(letter) or composed.get(letter)

    glyphs: Dict[str, Any] = {}
    for entry in STYLE_RECIPES[style]:
        letter = entry["letter"]
        if font_lookup(letter) is not None:
            raise SystemExit(f"{style}: font already has {letter}; drop it")
        recipe, glyph = _compose_entry(style, entry, lookup)
        composed[letter] = glyph
        glyphs[PINYIN_TONE_TO_NUMERIC[letter]] = {
            "letter": letter,
            "recipe": recipe,
            "glyph": glyph,
        }

    # Mark detection compares against the font's own plain letters, so
    # only bases may resolve to earlier overrides (e.g. the ɑ body of a).
    overrides: Dict[str, Any] = {}

    def base_lookup(letter: str) -> Optional[Dict[str, Any]]:
        if letter in overrides_by_letter:
            return overrides_by_letter[letter]
        return font_lookup(letter)

    overrides_by_letter: Dict[str, Dict[str, Any]] = {}
    for entry in STYLE_OVERRIDES.get(style, []):
        letter = entry["letter"]
        if font_lookup(letter) is None:
            raise SystemExit(f"{style}: font lacks {letter}; use STYLE_RECIPES")
        recipe, glyph = _override_entry(style, entry, font_lookup, base_lookup)
        overrides_by_letter[letter] = glyph
        overrides[PINYIN_TONE_TO_NUMERIC[letter]] = {
            "letter": letter,
            "recipe": recipe,
            "glyph": glyph,
        }

    bundle: Dict[str, Any] = {
        "font": font_path.name,
        "font_sha256": file_sha256(font_path),
        "glyphs": glyphs,
    }
    if overrides:
        bundle["overrides"] = overrides
    return bundle


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", choices=sorted(STYLE_RECIPES))
    args = parser.parse_args(argv)

    BUNDLED_GLYPHS_DIR.mkdir(parents=True, exist_ok=True)
    for style in [args.style] if args.style else sorted(STYLE_RECIPES):
        bundle = build_bundle(style)
        path = BUNDLED_GLYPHS_DIR / f"{style}.json"
        path.write_text(
            json.dumps(bundle, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        overridden = ", ".join(bundle.get("overrides", {})) or "-"
        print(
            f"{path.relative_to(ROOT)}: {', '.join(bundle['glyphs'])}"
            f" (overrides: {overridden})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
