# -*- coding: utf-8 -*-
# !/usr/bin/env python

"""
Pinyin processing utilities.

Contains functions for pinyin simplification and pronunciation handling.
"""

from __future__ import annotations

from functools import lru_cache

# ピンイン表記の簡略化、e.g.: wěi -> we3i
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


@lru_cache(maxsize=1024)
def simplification_pronunciation(pronunciation: str) -> str:
    """
    Simplify pinyin pronunciation with caching for performance.

    Converts pinyin with tone marks to simplified form.
    Example: wěi -> we3i

    Args:
        pronunciation: Pinyin with tone marks

    Returns:
        Simplified pinyin notation
    """
    try:
        return "".join([PINYIN_TONE_TO_NUMERIC[c] for c in pronunciation])
    except KeyError:
        # Handle missing characters gracefully
        result = []
        for c in pronunciation:
            result.append(PINYIN_TONE_TO_NUMERIC.get(c, c))
        return "".join(result)


def normalize_pinyin(pinyin: str) -> str:
    """
    Normalize pinyin by removing tone marks while preserving structure.

    Args:
        pinyin: Raw pinyin with possible tone marks

    Returns:
        Normalized pinyin without tone marks
    """
    # Map tone characters to base characters
    tone_mapping = {
        # a variations
        "ā": "a",
        "á": "a",
        "ǎ": "a",
        "à": "a",
        # e variations
        "ē": "e",
        "é": "e",
        "ě": "e",
        "è": "e",
        # i variations
        "ī": "i",
        "í": "i",
        "ǐ": "i",
        "ì": "i",
        # o variations
        "ō": "o",
        "ó": "o",
        "ǒ": "o",
        "ò": "o",
        # u variations
        "ū": "u",
        "ú": "u",
        "ǔ": "u",
        "ù": "u",
        # ü variations
        "ǖ": "ü",
        "ǘ": "ü",
        "ǚ": "ü",
        "ǜ": "ü",
        # m variations
        "m̄": "m",
        "ḿ": "m",
        "m̀": "m",
        # n variations
        "ń": "n",
        "ň": "n",
        "ǹ": "n",
    }

    result = []
    for char in pinyin:
        result.append(tone_mapping.get(char, char))

    return "".join(result)


def extract_tone_number(pinyin: str) -> int:
    """
    Extract tone number from pinyin with tone marks.

    Args:
        pinyin: Pinyin with tone marks

    Returns:
        Tone number (1-4), or 0 if neutral tone
    """
    tone_map = {
        # First tone (ā)
        "ā": 1,
        "ē": 1,
        "ī": 1,
        "ō": 1,
        "ū": 1,
        "ǖ": 1,
        "m̄": 1,
        # Second tone (á)
        "á": 2,
        "é": 2,
        "í": 2,
        "ó": 2,
        "ú": 2,
        "ǘ": 2,
        "ḿ": 2,
        "ń": 2,
        # Third tone (ǎ)
        "ǎ": 3,
        "ě": 3,
        "ǐ": 3,
        "ǒ": 3,
        "ǔ": 3,
        "ǚ": 3,
        "ň": 3,
        # Fourth tone (à)
        "à": 4,
        "è": 4,
        "ì": 4,
        "ò": 4,
        "ù": 4,
        "ǜ": 4,
        "m̀": 4,
        "ǹ": 4,
    }

    for char in pinyin:
        if char in tone_map:
            return tone_map[char]

    return 0  # Neutral tone
