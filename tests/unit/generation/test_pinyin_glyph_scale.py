"""Characterization tests for the scale matrix of pinyin letter references.

otfccbuild v0.9.6 / v0.10.4 keep glyphs whose references have ``a == d``
(verified with a full han_serif build), so no ``DELTA_4_REFLECTION`` offset is
needed: the pinyin letters must be scaled uniformly.
"""

from types import SimpleNamespace

import orjson
import pytest

from refactored.config import FontType
from refactored.generation import glyph_manager
from refactored.generation.glyph_manager import PinyinGlyphGenerator


def _font_config(avoid_overlapping: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        hanzi_canvas=SimpleNamespace(width=1000, height=1000),
        pinyin_canvas=SimpleNamespace(tracking=0),
        is_avoid_overlapping_mode=avoid_overlapping,
        x_scale_reduction_for_avoid_overlapping=0.1,
    )


@pytest.fixture
def generator(tmp_path):
    alphabet = {
        "n": {"advanceWidth": 500},
        "ǐ": {"advanceWidth": 500},
        "ǚ": {"advanceWidth": 500, "advanceHeight": 700},
    }
    path = tmp_path / "alphabet.json"
    path.write_bytes(orjson.dumps(alphabet))
    gen = PinyinGlyphGenerator(FontType.HAN_SERIF, _font_config())
    gen.load_alphabet_glyphs(path)
    return gen


def _references(generator, pronunciation="nǐ"):
    generator.generate_pronunciation_glyphs(
        hanzi_advance_width=1000,
        hanzi_advance_height=1000,
        pinyin_canvas_width=1000,
        pinyin_canvas_height=200,
        pinyin_canvas_base_line=800,
        all_pronunciations={pronunciation},
    )
    glyphs = generator.get_pronunciation_glyphs()
    assert len(glyphs) == 1
    return next(iter(glyphs.values()))["references"]


def test_pinyin_letters_are_scaled_uniformly(generator):
    references = _references(generator)

    assert references
    for ref in references:
        assert ref["a"] == ref["d"]
        assert ref["a"] > 0


def test_no_reflection_delta_offset_constant():
    assert not hasattr(glyph_manager, "DELTA_4_REFLECTION")
