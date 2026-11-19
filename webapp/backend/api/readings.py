# -*- coding: utf-8 -*-
"""Reading (pinyin) override endpoints."""

from __future__ import annotations

import unicodedata

from fastapi import APIRouter

from src.refactored.utils.pinyin_utils import (
    PINYIN_TONE_TO_NUMERIC,
    simplification_pronunciation,
    split_pinyin_letters,
)

from ..errors import problem
from ..schemas import Project, ReadingOverride
from ..services import custom_glyphs
from ..services.preview_composer import (
    _font_lock,
    _FontOutlines,
    get_base_pronunciations,
    get_pronunciations,
)
from .deps import get_project_or_404, store
from .projects import invalidate_build

router = APIRouter(prefix="/api/projects/{project_id}", tags=["readings"])


def _validate_pronunciations(project: Project, pronunciations: list[str]) -> None:
    if not pronunciations:
        raise problem(422, "reading_required", "At least one reading required")
    for pronunciation in pronunciations:
        simplified = simplification_pronunciation(pronunciation)
        if not simplified.replace("5", "").isascii():
            raise problem(
                422,
                "invalid_syllable",
                f"Invalid pinyin syllable: {pronunciation} — "
                "use tone-marked letters like zhōng",
                value=pronunciation,
            )
    if project.pinyin_font is None:
        return  # glyph coverage is checked once a pinyin font is chosen

    with _font_lock:
        outlines = _FontOutlines(project.pinyin_font.path, project.pinyin_font.sha256)
        available = custom_glyphs.available_letters(project, outlines)
    for pronunciation in pronunciations:
        for letter in split_pinyin_letters(pronunciation):
            if letter in PINYIN_TONE_TO_NUMERIC and letter not in available:
                raise problem(
                    422,
                    "missing_glyph",
                    f"The pinyin font has no glyph for '{letter}' "
                    f"(in {pronunciation}) — create it in the Glyphs step",
                    value=pronunciation,
                    letter=letter,
                    name=PINYIN_TONE_TO_NUMERIC[letter],
                )


def _effective(project: Project, char: str) -> dict:
    return {
        "char": char,
        "readings": get_pronunciations(project, char),
        "override": project.glyph_overrides.readings.get(char),
    }


@router.get("/readings/{char}")
def get_reading(project_id: str, char: str) -> dict:
    project = get_project_or_404(project_id)
    if len(char) != 1:
        raise problem(422, "one_char_required", "Specify exactly one character")
    return _effective(project, char)


@router.put("/readings/{char}")
def set_reading(project_id: str, char: str, body: ReadingOverride) -> dict:
    project = get_project_or_404(project_id)
    if len(char) != 1:
        raise problem(422, "one_char_required", "Specify exactly one character")
    # Store NFC so decomposed input matches base data and the letter table
    body = body.model_copy(
        update={
            "pronunciations": [
                unicodedata.normalize("NFC", p) for p in body.pronunciations
            ]
        }
    )
    _validate_pronunciations(project, body.pronunciations)

    before = project.glyph_overrides.readings.get(char)
    # A list identical to the base data is not an override
    if body.pronunciations == get_base_pronunciations(char):
        project.glyph_overrides.readings.pop(char, None)
    else:
        project.glyph_overrides.readings[char] = body
    if project.glyph_overrides.readings.get(char) != before:
        invalidate_build(project)
    store.save(project)
    return _effective(project, char)


@router.delete("/readings/{char}")
def delete_reading(project_id: str, char: str) -> dict:
    project = get_project_or_404(project_id)
    if char not in project.glyph_overrides.readings:
        raise problem(404, "no_override", f"No override for: {char}", char=char)
    del project.glyph_overrides.readings[char]
    invalidate_build(project)
    store.save(project)
    return _effective(project, char)
