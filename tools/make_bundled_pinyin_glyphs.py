# -*- coding: utf-8 -*-
"""Regenerate res/fonts/custom_pinyin_glyphs/<style>.json.

Composes the pinyin letters each builtin pinyin (latin) font lacks from
the font's own glyphs (base letter + the tone mark of an accented letter),
using the webapp's composer, and writes recipe + resulting otfcc glyph as
reviewable data. The core pipeline merges them into the alphabet JSON
(retrieve_latin_alphabet) only for letters the font lacks.

Usage (from the repository root):
    python tools/make_bundled_pinyin_glyphs.py [--style han_serif|handwritten]
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def recipe_for(entry: Dict[str, Any]) -> Dict[str, Any]:
    base, mark_source, flip_y = DEFAULT_RECIPES[entry["letter"]]
    return {
        "base": entry.get("base", base),
        "mark_source": entry.get("mark_source", mark_source),
        "mark_contours": entry.get("mark_contours"),
        "dx": float(entry.get("dx", 0.0)),
        "dy": float(entry.get("dy", 0.0)),
        "scale": float(entry.get("scale", 1.0)),
        "flip_y": bool(entry.get("flip_y", flip_y)),
    }


def build_bundle(style: str) -> Dict[str, Any]:
    font_path = FontConfig.get_alphabet_font_path(FontType(style))
    outlines = _FontOutlines(str(font_path), "bundle")
    composed: Dict[str, Dict[str, Any]] = {}

    def lookup(letter: str) -> Optional[Dict[str, Any]]:
        return font_glyph(outlines, letter) or composed.get(letter)

    glyphs: Dict[str, Any] = {}
    for entry in STYLE_RECIPES[style]:
        letter = entry["letter"]
        if font_glyph(outlines, letter) is not None:
            raise SystemExit(f"{style}: font already has {letter}; drop it")
        recipe = recipe_for(entry)
        base = lookup(recipe["base"])
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
        composed[letter] = result.glyph
        glyphs[PINYIN_TONE_TO_NUMERIC[letter]] = {
            "letter": letter,
            "recipe": recipe,
            "glyph": result.glyph,
        }

    return {
        "font": font_path.name,
        "font_sha256": file_sha256(font_path),
        "glyphs": glyphs,
    }


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
        print(f"{path.relative_to(ROOT)}: {', '.join(bundle['glyphs'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
