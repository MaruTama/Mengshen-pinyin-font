# -*- coding: utf-8 -*-
"""Pinyin letter coverage and custom (composed) letter glyphs."""

from __future__ import annotations

from fastapi import APIRouter

from ..errors import problem
from ..schemas import CustomGlyph, CustomGlyphRecipe, Project
from ..services import custom_glyphs
from ..services.glyph_composer import CompositionError, contours_to_svg_path
from ..services.preview_composer import _font_lock, _FontOutlines
from .deps import get_project_or_404, store
from .projects import invalidate_build

router = APIRouter(prefix="/api/projects/{project_id}", tags=["pinyin-letters"])


def _outlines(project: Project) -> _FontOutlines:
    if project.pinyin_font is None:
        raise problem(409, "no_font_selected", "No pinyin font selected", role="pinyin")
    return _FontOutlines(project.pinyin_font.path, project.pinyin_font.sha256)


def _letter_for(name: str) -> str:
    letter = custom_glyphs.LETTER_BY_NAME.get(name)
    if letter is None:
        raise problem(
            404, "unknown_letter", f"Unknown pinyin letter: {name}", name=name
        )
    return letter


def _compose(project: Project, outlines: _FontOutlines, recipe: CustomGlyphRecipe):
    try:
        return custom_glyphs.compose_letter(project, outlines, recipe)
    except CompositionError as e:
        raise problem(422, e.code, str(e))


@router.get("/pinyin-letters")
def list_letters(project_id: str) -> dict:
    project = get_project_or_404(project_id)
    with _font_lock:
        outlines = _outlines(project)
        hhea = outlines.font["hhea"]
        return {
            "upem": outlines.upem,
            "ascent": float(hhea.ascender),
            "descent": abs(float(hhea.descender)),
            "letters": custom_glyphs.letter_rows(project, outlines),
        }


@router.post("/pinyin-letters/{name}/preview")
def preview_letter(project_id: str, name: str, body: CustomGlyphRecipe) -> dict:
    """Compose without saving (live preview while adjusting)."""
    project = get_project_or_404(project_id)
    letter = _letter_for(name)
    with _font_lock:
        outlines = _outlines(project)
        result = _compose(project, outlines, body)
        source = custom_glyphs.lookup_glyph(project, outlines, body.mark_source)
        hhea = outlines.font["hhea"]
        contours = result.glyph["contours"]
        split = result.base_contour_count
        return {
            "letter": letter,
            "name": name,
            "glyph": result.glyph,
            "advance_width": result.glyph["advanceWidth"],
            "base_path": contours_to_svg_path(contours[:split]),
            "mark_path": contours_to_svg_path(contours[split:]),
            "mark_contours": result.mark_contours,
            "source_contour_count": len(source["contours"]) if source else 0,
            "auto_dx": result.auto_dx,
            "auto_dy": result.auto_dy,
            "upem": outlines.upem,
            "ascent": float(hhea.ascender),
            "descent": abs(float(hhea.descender)),
        }


@router.put("/pinyin-letters/{name}")
def save_letter(project_id: str, name: str, body: CustomGlyphRecipe) -> dict:
    project = get_project_or_404(project_id)
    letter = _letter_for(name)
    with _font_lock:
        outlines = _outlines(project)
        if custom_glyphs.font_has(outlines, letter):
            raise problem(
                409,
                "letter_in_font",
                f"The pinyin font already has: {letter}",
                letter=letter,
            )
        result = _compose(project, outlines, body)
    # _outlines() guarantees a pinyin font
    font_sha256 = project.pinyin_font.sha256 if project.pinyin_font else ""
    project.glyph_overrides.custom_glyphs[name] = CustomGlyph(
        letter=letter,
        recipe=body,
        font_sha256=font_sha256,
        glyph=result.glyph,
    )
    invalidate_build(project)
    store.save(project)
    with _font_lock:
        return custom_glyphs.letter_row(project, outlines, letter)


@router.delete("/pinyin-letters/{name}")
def delete_letter(project_id: str, name: str) -> dict:
    project = get_project_or_404(project_id)
    letter = _letter_for(name)
    if name not in project.glyph_overrides.custom_glyphs:
        raise problem(404, "no_custom_glyph", f"No custom glyph for: {letter}")
    del project.glyph_overrides.custom_glyphs[name]
    invalidate_build(project)
    store.save(project)
    with _font_lock:
        outlines = _outlines(project) if project.pinyin_font else None
        return custom_glyphs.letter_row(project, outlines, letter)
