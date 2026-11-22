# -*- coding: utf-8 -*-
"""Readings restored to overwrite.txt and pinyin letter glyph coverage."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import pytest

from src.refactored.utils.pinyin_utils import (
    PINYIN_TONE_TO_NUMERIC,
    split_pinyin_letters,
)

ROOT = Path(__file__).resolve().parents[3]
MERGED = ROOT / "outputs" / "merged-mapping-table.txt"
ALPHABET_JSON = ROOT / "tmp" / "json" / "alphabet_for_pinyin_{style}.json"

# Expected merged readings: pinyin-data order first, overwrite-only readings after
EXPECTED = {
    "呣": ["ḿ", "m̀", "móu"],
    "哏": ["gén", "hěn", "ǹ", "hēn"],
    "哽": ["gěng", "ńg", "ń"],
    "唔": ["wú", "wù", "ńg", "ḿ", "ń"],
    "嗯": ["ń", "ńg", "ňg", "ǹg", "ň", "ǹ", "en"],
    "嘸": ["fǔ", "wǔ", "m̄", "ḿ"],
    "欸": ["āi", "ǎi", "ê̄", "ế", "ê̌", "ề", "ěi", "èi"],
    "誒": ["éi", "xī", "ê̄", "ế", "ê̌", "ěi", "ề", "èi", "ēi", "ê"],
    # Issue #30 (only éi is in pinyin-data; the rest are overwrite-only)
    "诶": ["éi", "ēi", "ěi", "èi"],
}


def _table(path: Path) -> dict[str, list[str]]:
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("U+") or ":" not in line:
            continue
        code, rest = line.split(":", 1)
        readings = [p.strip() for p in rest.split("#")[0].split(",") if p.strip()]
        table[chr(int(code[2:], 16))] = readings
    return table


@pytest.mark.parametrize("char", list(EXPECTED))
def test_restored_readings(char):
    # Checked on the merged table: a reading may come from pinyin-data or
    # overwrite.txt (overwrite lines identical to pinyin-data are removed, #62).
    expected = [unicodedata.normalize("NFC", p) for p in EXPECTED[char]]
    assert _table(MERGED)[char] == expected


def test_readings_are_nfc_and_representable():
    for char, readings in _table(MERGED).items():
        for reading in readings:
            assert unicodedata.normalize("NFC", reading) == reading, char
            for letter in split_pinyin_letters(reading):
                assert letter in PINYIN_TONE_TO_NUMERIC, (char, reading, letter)


def test_no_capitalized_readings():
    for char, readings in _table(MERGED).items():
        assert all(r == r.lower() for r in readings), char


@pytest.mark.parametrize("style", ["han_serif", "handwritten"])
def test_every_used_letter_has_a_glyph(style):
    """Guards against letters silently dropped from the built pinyin."""
    path = Path(str(ALPHABET_JSON).format(style=style))
    alphabet = json.loads(path.read_text(encoding="utf-8"))
    available = {PINYIN_TONE_TO_NUMERIC.get(letter, letter) for letter in alphabet}
    used = {
        letter
        for readings in _table(MERGED).values()
        for reading in readings
        for letter in split_pinyin_letters(reading)
    }
    missing = sorted(
        letter for letter in used if PINYIN_TONE_TO_NUMERIC[letter] not in available
    )
    assert missing == []
