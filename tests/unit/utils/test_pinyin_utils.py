# -*- coding: utf-8 -*-
"""Tests for pinyin simplification (tone marks -> ASCII glyph-name parts)."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pytest

from src.refactored.utils.pinyin_utils import (
    PINYIN_TONE_TO_NUMERIC,
    simplification_pronunciation,
    split_pinyin_letters,
)

# Frozen copy of the single-code-point mapping before ê-family support.
# Characterization: these must keep producing byte-identical names.
LEGACY_SINGLE_CODEPOINT = {
    "a": "a", "ā": "a1", "á": "a2", "ǎ": "a3", "à": "a4",
    "b": "b", "c": "c", "d": "d",
    "e": "e", "ē": "e1", "é": "e2", "ě": "e3", "è": "e4",
    "f": "f", "g": "g", "h": "h",
    "i": "i", "ī": "i1", "í": "i2", "ǐ": "i3", "ì": "i4",
    "j": "j", "k": "k", "l": "l",
    "m": "m", "ḿ": "m2",
    "n": "n", "ń": "n2", "ň": "n3", "ǹ": "n4",
    "o": "o", "ō": "o1", "ó": "o2", "ǒ": "o3", "ò": "o4",
    "p": "p", "q": "q", "r": "r", "s": "s", "t": "t",
    "u": "u", "ū": "u1", "ú": "u2", "ǔ": "u3", "ù": "u4",
    "ü": "v", "ǖ": "v1", "ǘ": "v2", "ǚ": "v3", "ǜ": "v4",
    "v": "v", "w": "w", "x": "x", "y": "y", "z": "z",
}  # fmt: skip

MERGED_TABLE = (
    Path(__file__).resolve().parents[3] / "outputs" / "merged-mapping-table.txt"
)


def _legacy_simplify(pronunciation: str) -> str:
    return "".join(LEGACY_SINGLE_CODEPOINT.get(c, c) for c in pronunciation)


def _all_syllables() -> set[str]:
    syllables: set[str] = set()
    for line in MERGED_TABLE.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or ":" not in line:
            continue
        rhs = line.split(":", 1)[1].split("#")[0]
        syllables.update(rhs.replace(",", " ").split())
    return syllables


class TestCharacterization:
    @pytest.mark.parametrize("letter,expected", LEGACY_SINGLE_CODEPOINT.items())
    def test_existing_letters_unchanged(self, letter, expected):
        assert PINYIN_TONE_TO_NUMERIC[letter] == expected
        assert simplification_pronunciation(letter) == expected

    def test_existing_multi_codepoint_m_unchanged(self):
        assert simplification_pronunciation("m̄") == "m1"
        assert simplification_pronunciation("m̀") == "m4"

    @pytest.mark.skipif(not MERGED_TABLE.exists(), reason="merged table missing")
    def test_every_real_syllable_byte_identical(self):
        syllables = _all_syllables()
        assert len(syllables) > 1000
        for syllable in syllables:
            assert simplification_pronunciation(syllable) == _legacy_simplify(
                syllable
            ), syllable

    def test_wei3(self):
        assert simplification_pronunciation("wěi") == "we3i"

    def test_unknown_characters_pass_through(self):
        assert simplification_pronunciation("漢5") == "漢5"


class TestEhFamily:
    @pytest.mark.parametrize(
        "letter,expected",
        [
            ("ê", "eh"),
            ("ê̄", "eh1"),
            ("ế", "eh2"),
            ("ê̌", "eh3"),
            ("ề", "eh4"),
        ],
    )
    def test_eh_letters(self, letter, expected):
        assert PINYIN_TONE_TO_NUMERIC[letter] == expected
        assert simplification_pronunciation(letter) == expected

    def test_nfd_input_is_normalized(self):
        # ế typed as e + circumflex + acute (fully decomposed)
        assert simplification_pronunciation("ế") == "eh2"
        # ē typed decomposed
        assert simplification_pronunciation("ē") == "e1"

    def test_multi_codepoint_matched_before_single(self):
        # ê̄ must not become "eh" + stray combining macron
        assert simplification_pronunciation("ê̄") == "eh1"
        assert simplification_pronunciation("ê̌") == "eh3"

    def test_all_simplified_names_ascii(self):
        for letter, simplified in PINYIN_TONE_TO_NUMERIC.items():
            assert simplified.isascii(), letter
            assert unicodedata.normalize("NFC", letter) == letter

    def test_simplified_names_unique(self):
        values = list(PINYIN_TONE_TO_NUMERIC.values())
        # ü and v intentionally share "v"
        assert len(values) - len(set(values)) == 1

    @pytest.mark.skipif(not MERGED_TABLE.exists(), reason="merged table missing")
    def test_eh_names_cannot_collide_with_real_syllables(self):
        simplified = {simplification_pronunciation(s) for s in _all_syllables()}
        assert not any("eh" in name for name in simplified)


class TestSplitLetters:
    def test_plain(self):
        assert split_pinyin_letters("zhōng") == ["z", "h", "ō", "n", "g"]

    def test_combining_marks_attach(self):
        assert split_pinyin_letters("m̄") == ["m̄"]
        assert split_pinyin_letters("ê̄") == ["ê̄"]
        assert split_pinyin_letters("ế") == ["ế"]

    def test_empty(self):
        assert split_pinyin_letters("") == []
