# -*- coding: utf-8 -*-
"""Pinyin letter glyph naming and grapheme-aware layout."""

from __future__ import annotations

import json

import pytest

from src.refactored.config.font_config import FontConfig, FontType
from src.refactored.generation.glyph_manager import PinyinGlyphGenerator
from src.refactored.scripts.retrieve_latin_alphabet import (
    ALPHABET,
    OPTIONAL_ALPHABET,
    REQUIRED_ALPHABET,
)

LEGACY_ALPHABET = (
    "a ā á ǎ à b c d e ē é ě è f g h i ī í ǐ ì j k l m ḿ n ń ň ǹ "
    "o ō ó ǒ ò p q r s t u ū ú ǔ ù ü ǖ ǘ ǚ ǜ v w x y z"
).split()


def _glyph(width: float = 500.0) -> dict:
    return {"advanceWidth": width, "contours": []}


def _generator() -> PinyinGlyphGenerator:
    config = FontConfig.get_config(FontType.HAN_SERIF)
    return PinyinGlyphGenerator(FontType.HAN_SERIF, config)


def _generate(generator: PinyinGlyphGenerator, pronunciations: set[str]) -> dict:
    config = generator.font_config
    generator.generate_pronunciation_glyphs(
        hanzi_advance_width=1000.0,
        hanzi_advance_height=1000.0,
        pinyin_canvas_width=config.pinyin_canvas.width,
        pinyin_canvas_height=config.pinyin_canvas.height,
        pinyin_canvas_base_line=config.pinyin_canvas.base_line,
        all_pronunciations=pronunciations,
    )
    return generator.get_pronunciation_glyphs()


class TestAlphabet:
    def test_legacy_letters_kept_in_order(self):
        assert [c for c in ALPHABET if c not in OPTIONAL_ALPHABET] == LEGACY_ALPHABET

    def test_precomposed_eh_letters_added(self):
        assert OPTIONAL_ALPHABET == ("ê", "ế", "ề")
        for letter in OPTIONAL_ALPHABET:
            assert letter in ALPHABET

    def test_required_alphabet_excludes_optional(self):
        assert REQUIRED_ALPHABET == LEGACY_ALPHABET

    def test_all_single_code_point(self):
        assert all(len(c) == 1 for c in ALPHABET)


class TestLoadAlphabetGlyphs:
    def test_names_from_table(self, tmp_path):
        data = {
            letter: _glyph()
            for letter in LEGACY_ALPHABET + ["ê", "ê̄", "ế", "ê̌", "ề"] + ["m̄", "m̀"]
        }
        path = tmp_path / "alphabet.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        generator = _generator()
        generator.load_alphabet_glyphs(path)
        names = set(generator.get_pinyin_alphabets())

        for expected in [
            "py_alphabet_a",
            "py_alphabet_a1",
            "py_alphabet_v",
            "py_alphabet_v3",
            "py_alphabet_m2",
            "py_alphabet_n4",
            "py_alphabet_eh",
            "py_alphabet_eh1",
            "py_alphabet_eh2",
            "py_alphabet_eh3",
            "py_alphabet_eh4",
            "py_alphabet_m1",
            "py_alphabet_m4",
        ]:
            assert expected in names
        assert all(name.isascii() for name in names)
        assert len(names) == len(data) - 1  # ü and v share py_alphabet_v


class TestGraphemeLayout:
    @pytest.fixture
    def generator(self):
        generator = _generator()
        generator.set_alphabet_glyphs(
            {
                name: {"advanceWidth": 500.0, "advanceHeight": 1000.0}
                for name in [
                    "py_alphabet_v3",
                    "py_alphabet_e1",
                    "py_alphabet_eh1",
                    "py_alphabet_m1",
                    "py_alphabet_n",
                    "py_alphabet_g",
                    "py_alphabet_h",
                    "py_alphabet_z",
                    "py_alphabet_o1",
                ]
            }
        )
        return generator

    def test_multi_codepoint_letter_is_one_slot(self, generator):
        glyphs = _generate(generator, {"ê̄", "ē", "m̄"})
        eh1 = glyphs["eh1"]["references"]
        e1 = glyphs["e1"]["references"]
        m1 = glyphs["m1"]["references"]
        assert [r["glyph"] for r in eh1] == ["py_alphabet_eh1"]
        assert [r["glyph"] for r in m1] == ["py_alphabet_m1"]
        assert eh1[0]["x"] == e1[0]["x"] == m1[0]["x"]

    def test_multi_codepoint_inside_syllable(self, generator):
        e_circumflex_macron = "ê̄"
        glyphs = _generate(generator, {e_circumflex_macron + "ng", "ēng"})
        assert [r["glyph"] for r in glyphs["eh1ng"]["references"]] == [
            "py_alphabet_eh1",
            "py_alphabet_n",
            "py_alphabet_g",
        ]
        assert [r["x"] for r in glyphs["eh1ng"]["references"]] == [
            r["x"] for r in glyphs["e1ng"]["references"]
        ]

    def test_existing_syllable_positions_unchanged(self, generator):
        glyphs = _generate(generator, {"zhōng"})
        refs = glyphs["zho1ng"]["references"]
        assert [r["glyph"] for r in refs] == [
            "py_alphabet_z",
            "py_alphabet_h",
            "py_alphabet_o1",
            "py_alphabet_n",
            "py_alphabet_g",
        ]
        # Characterization: captured from the pre-grapheme implementation
        assert [r["x"] for r in refs] == [101.58, 265.38, 429.18, 592.97, 756.76]
