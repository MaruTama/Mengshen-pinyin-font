# -*- coding: utf-8 -*-
# !/usr/bin/env python

"""
Character processing utilities.

Contains functions for converting between different character representations
and working with Unicode values.
"""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=2048)
def hanzi_to_unicode_str(hanzi: str) -> str:
    """
    Convert hanzi character to Unicode string representation.

    Args:
        hanzi: Single Chinese character

    Returns:
        Unicode value as string (e.g., "20013" for "中")
    """
    if not hanzi or len(hanzi) != 1:
        raise ValueError(f"Expected single character, got: {hanzi}")

    return str(ord(hanzi))


@lru_cache(maxsize=2048)
def unicode_str_to_hanzi(unicode_str: str) -> str:
    """
    Convert Unicode string representation to hanzi character.

    Args:
        unicode_str: Unicode value as string (e.g., "20013")

    Returns:
        Single Chinese character
    """
    try:
        unicode_value = int(unicode_str)
        return chr(unicode_value)
    except ValueError:
        raise ValueError(f"Invalid Unicode string: {unicode_str}")
    except ValueError:  # chr() range error
        raise ValueError(f"Unicode value out of range: {unicode_value}")


def is_hanzi(char: str) -> bool:
    """
    Check if a character is a Chinese hanzi.

    Uses Unicode ranges for CJK characters.

    Args:
        char: Single character to check

    Returns:
        True if character is hanzi, False otherwise
    """
    if not char or len(char) != 1:
        return False

    code = ord(char)

    # CJK Unified Ideographs
    if 0x4E00 <= code <= 0x9FFF:
        return True

    # CJK Extension A
    if 0x3400 <= code <= 0x4DBF:
        return True

    # CJK Extension B
    if 0x20000 <= code <= 0x2A6DF:
        return True

    # CJK Extension C
    if 0x2A700 <= code <= 0x2B73F:
        return True

    # CJK Extension D
    if 0x2B740 <= code <= 0x2B81F:
        return True

    # CJK Extension E
    if 0x2B820 <= code <= 0x2CEAF:
        return True

    return False


def is_hiragana(char: str) -> bool:
    """
    Check if a character is hiragana.

    Args:
        char: Single character to check

    Returns:
        True if character is hiragana, False otherwise
    """
    if not char or len(char) != 1:
        return False

    code = ord(char)
    return 0x3040 <= code <= 0x309F


def is_katakana(char: str) -> bool:
    """
    Check if a character is katakana.

    Args:
        char: Single character to check

    Returns:
        True if character is katakana, False otherwise
    """
    if not char or len(char) != 1:
        return False

    code = ord(char)
    return 0x30A0 <= code <= 0x30FF


def is_cjk_character(char: str) -> bool:
    """
    Check if a character is any CJK character (hanzi, hiragana, katakana).

    Args:
        char: Single character to check

    Returns:
        True if character is CJK, False otherwise
    """
    return is_hanzi(char) or is_hiragana(char) or is_katakana(char)


def normalize_unicode_variant(char: str) -> str:
    """
    Normalize Unicode variants to their base form.

    Handles cases where the same character might have multiple Unicode representations.

    Args:
        char: Character to normalize

    Returns:
        Normalized character
    """
    # For now, just return the character as-is
    # This can be extended later if specific normalization is needed
    return char
