# -*- coding: utf-8 -*-
# !/usr/bin/env python

"""
Pinyin processing utilities.

Contains functions for pinyin simplification and pronunciation handling.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from typing import List

# ピンイン表記の簡略化、e.g.: wěi -> we3i
#
# Keys are NFC-normalized pinyin letters (one grapheme each; some have no
# precomposed code point, e.g. m̄ = m + U+0304). Values are ASCII-only and
# become glyph names (py_alphabet_<value>).
#
# ê-family naming scheme: ê -> "eh", tones -> "eh1".."eh4" (ê̄ ế ê̌ ề).
# Collision-free: in pinyin, "h" only ever starts a syllable or follows
# z/c/s (zh/ch/sh), never a vowel, so no simplified syllable can contain
# "eh" (verified against outputs/merged-mapping-table.txt in
# tests/unit/utils/test_pinyin_utils.py).
PINYIN_TONE_TO_NUMERIC = {
    "a": "a",
    "ā": "a1",
    "á": "a2",
    "ǎ": "a3",
    "à": "a4",
    "b": "b",
    "c": "c",
    "d": "d",
    "e": "e",
    "ē": "e1",
    "é": "e2",
    "ě": "e3",
    "è": "e4",
    "\u00ea": "eh",  # ê
    "\u00ea\u0304": "eh1",  # ê̄ (no precomposed code point)
    "\u1ebf": "eh2",  # ế
    "\u00ea\u030c": "eh3",  # ê̌ (no precomposed code point)
    "\u1ec1": "eh4",  # ề
    "f": "f",
    "g": "g",
    "h": "h",
    "i": "i",
    "ī": "i1",
    "í": "i2",
    "ǐ": "i3",
    "ì": "i4",
    "j": "j",
    "k": "k",
    "l": "l",
    "m": "m",
    "m̄": "m1",
    "ḿ": "m2",
    "m̀": "m4",
    "n": "n",
    "ń": "n2",
    "ň": "n3",
    "ǹ": "n4",
    "o": "o",
    "ō": "o1",
    "ó": "o2",
    "ǒ": "o3",
    "ò": "o4",
    "p": "p",
    "q": "q",
    "r": "r",
    "s": "s",
    "t": "t",
    "u": "u",
    "ū": "u1",
    "ú": "u2",
    "ǔ": "u3",
    "ù": "u4",
    "ü": "v",
    "ǖ": "v1",
    "ǘ": "v2",
    "ǚ": "v3",
    "ǜ": "v4",
    "v": "v",
    "w": "w",
    "x": "x",
    "y": "y",
    "z": "z",
}


def split_pinyin_letters(text: str) -> List[str]:
    """Split pinyin into letters (graphemes), NFC-normalized.

    Combining marks attach to the preceding base character, so letters
    without a precomposed code point (ê̄, ê̌, m̄, m̀) stay one unit.
    """
    letters: List[str] = []
    for char in unicodedata.normalize("NFC", text):
        if letters and unicodedata.combining(char):
            letters[-1] += char
        else:
            letters.append(char)
    return letters


@lru_cache(maxsize=1024)
def simplification_pronunciation(pronunciation: str) -> str:
    """
    Simplify pinyin pronunciation with caching for performance.

    Converts pinyin with tone marks to simplified form, letter by letter
    (grapheme-aware, so multi-code-point letters map as a whole).
    Example: wěi -> we3i, ê̄ -> eh1

    Args:
        pronunciation: Pinyin with tone marks

    Returns:
        Simplified pinyin notation; unknown letters pass through unchanged
    """
    return "".join(
        PINYIN_TONE_TO_NUMERIC.get(letter, letter)
        for letter in split_pinyin_letters(pronunciation)
    )
