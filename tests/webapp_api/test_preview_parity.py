# -*- coding: utf-8 -*-
"""Preview placement must match the production PinyinGlyphGenerator math."""

from __future__ import annotations

import pytest

from src.refactored.config.font_config import FontConfig, FontType
from src.refactored.generation.glyph_manager import PinyinGlyphGenerator
from src.refactored.utils.pinyin_utils import simplification_pronunciation
from webapp.backend.schemas import (
    CanvasModel,
    HanziCanvasModel,
    PinyinCanvasModel,
)
from webapp.backend.services.preview_composer import _pinyin_references

HANZI_WIDTH = 1000.0
HANZI_HEIGHT = 1000.0

ALPHABET_GLYPHS = {
    name: {"advanceWidth": 500.0, "advanceHeight": 1000.0}
    for name in [
        "py_alphabet_n",
        "py_alphabet_i3",
        "py_alphabet_z",
        "py_alphabet_h",
        "py_alphabet_u",
        "py_alphabet_a1",
        "py_alphabet_g",
        "py_alphabet_v3",
    ]
}


def han_serif_canvas() -> CanvasModel:
    config = FontConfig.get_config(FontType.HAN_SERIF)
    return CanvasModel(
        pinyin=PinyinCanvasModel(
            width=config.pinyin_canvas.width,
            height=config.pinyin_canvas.height,
            base_line=config.pinyin_canvas.base_line,
            tracking=config.pinyin_canvas.tracking,
        ),
        hanzi=HanziCanvasModel(
            width=config.hanzi_canvas.width,
            height=config.hanzi_canvas.height,
        ),
        is_avoid_overlapping_mode=config.is_avoid_overlapping_mode,
        x_scale_reduction_for_avoid_overlapping=(
            config.x_scale_reduction_for_avoid_overlapping
        ),
    )


def reference_from_production(pronunciation: str) -> list:
    """Run PinyinGlyphGenerator directly with the HAN_SERIF preset."""
    config = FontConfig.get_config(FontType.HAN_SERIF)
    generator = PinyinGlyphGenerator(FontType.HAN_SERIF, config)
    generator.set_alphabet_glyphs(ALPHABET_GLYPHS)
    generator.generate_pronunciation_glyphs(
        hanzi_advance_width=HANZI_WIDTH,
        hanzi_advance_height=HANZI_HEIGHT,
        pinyin_canvas_width=config.pinyin_canvas.width,
        pinyin_canvas_height=config.pinyin_canvas.height,
        pinyin_canvas_base_line=config.pinyin_canvas.base_line,
        all_pronunciations={pronunciation},
    )
    simplified = simplification_pronunciation(pronunciation)
    return list(generator.get_pronunciation_glyphs()[simplified]["references"])


class _FakeProject:
    """Minimal stand-in: _pinyin_references only reads canvas via model_copy."""

    def __init__(self, canvas: CanvasModel):
        self.canvas = canvas

    def model_copy(self, update):
        clone = _FakeProject(self.canvas)
        clone.canvas = update.get("canvas", self.canvas)
        return clone


@pytest.mark.parametrize("pronunciation", ["nǐ", "zhuāng"])
def test_preview_references_match_production(pronunciation: str):
    canvas = han_serif_canvas()
    preview_refs = _pinyin_references(
        pronunciation,
        HANZI_WIDTH,
        HANZI_HEIGHT,
        canvas,
        _FakeProject(canvas),
        ALPHABET_GLYPHS,
    )
    production_refs = reference_from_production(pronunciation)

    assert len(preview_refs) == len(production_refs) > 0
    for preview_ref, production_ref in zip(preview_refs, production_refs):
        for key in ("glyph", "x", "y", "a", "d"):
            assert preview_ref[key] == production_ref[key], key
