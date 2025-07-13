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
