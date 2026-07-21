# -*- coding: utf-8 -*-
"""Reading (pinyin) override endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from src.refactored.utils.pinyin_utils import simplification_pronunciation

from ..errors import problem
from ..schemas import Project, ReadingOverride
from ..services.preview_composer import get_base_pronunciations, get_pronunciations
from .deps import get_project_or_404, store
from .projects import invalidate_build

router = APIRouter(prefix="/api/projects/{project_id}", tags=["readings"])


def _validate_pronunciations(pronunciations: list[str]) -> None:
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
    _validate_pronunciations(body.pronunciations)

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
