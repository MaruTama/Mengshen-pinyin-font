# -*- coding: utf-8 -*-
"""Custom pinyin letter glyphs: lookup, composition and status per project.

A pinyin font often lacks some letters real readings need (ê-family, m̄,
m̀, ...). The user composes them from glyphs the font does have (a base
letter + the tone mark of an accented letter); see glyph_composer for the
geometry. Custom glyphs are tied to the pinyin font they were composed
from (``font_sha256``) and only fill letters that font lacks.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Dict, List, Optional, Protocol, Tuple

from src.refactored.utils.pinyin_utils import PINYIN_TONE_TO_NUMERIC

from ..schemas import CustomGlyph, CustomGlyphRecipe, Project
from . import glyph_composer
from .glyph_composer import Composition, CompositionError, Glyph

# Letter -> (base letter, mark source letter, flip_y) prefilled in the UI.
# ê has no circumflex source in fonts lacking it: a vertically mirrored
# caron (from ě) serves as the circumflex.
DEFAULT_RECIPES: Dict[str, Tuple[str, str, bool]] = {
    "ê": ("e", "ě", True),  # ê  = e + mirrored caron of ě
    "ê̄": ("ê", "ē", False),  # ê̄ = ê + macron of ē
    "ế": ("ê", "é", False),  # ế  = ê + acute of é
    "ê̌": ("ê", "ě", False),  # ê̌ = ê + caron of ě
    "ề": ("ê", "è", False),  # ề  = ê + grave of è
    "m̄": ("m", "ē", False),  # m̄
    "ḿ": ("m", "é", False),  # ḿ
    "m̀": ("m", "è", False),  # m̀
    "ń": ("n", "é", False),  # ń
    "ň": ("n", "ě", False),  # ň
    "ǹ": ("n", "è", False),  # ǹ
}

# simplified ASCII name (e.g. "eh1") -> letter; "v" resolves to plain v
LETTER_BY_NAME: Dict[str, str] = {
    name: letter for letter, name in PINYIN_TONE_TO_NUMERIC.items()
}


class FontOutlines(Protocol):
    """The subset of preview_composer._FontOutlines used here."""

    font: Any
    glyph_set: Any
    upem: int

    def glyph_name(self, char: str) -> Optional[str]: ...

    def advance_width(self, glyph_name: str) -> float: ...


def font_has(outlines: Optional[FontOutlines], letter: str) -> bool:
    if outlines is None or len(letter) != 1:
        return False
    return outlines.glyph_name(letter) is not None


def font_glyph(outlines: FontOutlines, letter: str) -> Optional[Glyph]:
    """The font's glyph for a letter as an otfcc-format glyph.

    Components are decomposed and cubic (CFF) outlines converted to
    quadratic, so the result is always TrueType-style contours.
    """
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    if len(letter) != 1:
        return None
    glyph_name = outlines.glyph_name(letter)
    if glyph_name is None:
        return None

    recorder = DecomposingRecordingPen(outlines.glyph_set)
    outlines.glyph_set[glyph_name].draw(recorder)
    tt_pen = TTGlyphPen(None)
    if "glyf" in outlines.font:
        recorder.replay(tt_pen)
    else:
        recorder.replay(Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=True))
    glyph = tt_pen.glyph()

    contours: List[List[Dict[str, Any]]] = []
    if glyph.numberOfContours > 0:
        coordinates = list(glyph.coordinates)
        start = 0
        for end in glyph.endPtsOfContours:
            contours.append(
                [
                    {
                        "x": int(round(coordinates[i][0])),
                        "y": int(round(coordinates[i][1])),
                        "on": bool(glyph.flags[i] & 1),
                    }
                    for i in range(start, end + 1)
                ]
            )
            start = end + 1
    return {"advanceWidth": outlines.advance_width(glyph_name), "contours": contours}


def active_custom_glyphs(project: Optional[Project]) -> Dict[str, CustomGlyph]:
    """Custom glyphs composed from the currently selected pinyin font."""
    if project is None or project.pinyin_font is None:
        return {}
    sha = project.pinyin_font.sha256
    return {
        name: custom
        for name, custom in project.glyph_overrides.custom_glyphs.items()
        if custom.font_sha256 == sha
    }


def custom_glyphs_in_use(
    project: Optional[Project], outlines: Optional[FontOutlines]
) -> Dict[str, CustomGlyph]:
    """Active custom glyphs for letters the pinyin font itself lacks."""
    return {
        name: custom
        for name, custom in active_custom_glyphs(project).items()
        if not font_has(outlines, custom.letter)
    }


def lookup_glyph(
    project: Optional[Project], outlines: FontOutlines, letter: str
) -> Optional[Glyph]:
    """Font glyph for the letter, else an active custom glyph."""
    letter = unicodedata.normalize("NFC", letter)
    glyph = font_glyph(outlines, letter)
    if glyph is not None:
        return glyph
    for custom in active_custom_glyphs(project).values():
        if custom.letter == letter:
            return custom.glyph
    return None


def available_letters(
    project: Optional[Project], outlines: Optional[FontOutlines]
) -> set[str]:
    """Pinyin letters that have a glyph (in the font or custom)."""
    letters = {
        letter for letter in PINYIN_TONE_TO_NUMERIC if font_has(outlines, letter)
    }
    letters.update(c.letter for c in active_custom_glyphs(project).values())
    return letters


def compose_letter(
    project: Optional[Project], outlines: FontOutlines, recipe: CustomGlyphRecipe
) -> Composition:
    """Compose a glyph per the recipe from the project's pinyin glyphs."""
    base = lookup_glyph(project, outlines, recipe.base)
    if base is None:
        raise CompositionError(
            "glyph_unavailable", f"No glyph for base letter: {recipe.base}"
        )
    source = lookup_glyph(project, outlines, recipe.mark_source)
    if source is None:
        raise CompositionError(
            "glyph_unavailable", f"No glyph for mark source: {recipe.mark_source}"
        )
    plain_letter = unicodedata.normalize("NFD", recipe.mark_source)[:1]
    plain = (
        lookup_glyph(project, outlines, plain_letter)
        if plain_letter and plain_letter != recipe.mark_source
        else None
    )
    return glyph_composer.compose(
        base,
        source,
        plain,
        glyph_composer.Recipe(
            dx=recipe.dx,
            dy=recipe.dy,
            scale=recipe.scale,
            flip_y=recipe.flip_y,
            mark_contours=recipe.mark_contours,
        ),
    )


def default_recipe(letter: str) -> Optional[CustomGlyphRecipe]:
    defaults = DEFAULT_RECIPES.get(letter)
    if defaults is None:
        return None
    base, mark_source, flip_y = defaults
    return CustomGlyphRecipe(base=base, mark_source=mark_source, flip_y=flip_y)


def letter_row(
    project: Project, outlines: Optional[FontOutlines], letter: str
) -> Dict[str, Any]:
    """Status of one pinyin letter: in font / custom / missing."""
    name = PINYIN_TONE_TO_NUMERIC[letter]
    stored = project.glyph_overrides.custom_glyphs.get(name)
    active = active_custom_glyphs(project).get(name)
    if font_has(outlines, letter):
        status = "font"
    elif active is not None:
        status = "custom"
    else:
        status = "missing"
    default = default_recipe(letter)
    return {
        "letter": letter,
        "name": name,
        "status": status,
        "stale": stored is not None and active is None,
        "default_recipe": default.model_dump() if default else None,
        "recipe": stored.recipe.model_dump() if stored else None,
    }


def letter_rows(project: Project, outlines: Optional[FontOutlines]) -> List[dict]:
    return [letter_row(project, outlines, letter) for letter in PINYIN_TONE_TO_NUMERIC]
