# -*- coding: utf-8 -*-
# !/usr/bin/env python

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterator, List

from ..data.pinyin_data import get_pinyin_table_with_mapping_table


@dataclass
class HanziPinyin:
    """Represents a Chinese character with its pinyin pronunciations.

    Supports tuple unpacking for backward compatibility:
        hanzi, pinyins = HanziPinyin('中', ['zhōng', 'zhòng'])
    """

    character: str
    pronunciations: List[str]

    @property
    def is_single_pronunciation(self) -> bool:
        """Check if the character has only one pronunciation."""
        return len(self.pronunciations) == 1

    @property
    def is_multiple_pronunciation(self) -> bool:
        """Check if the character has multiple pronunciations."""
        return len(self.pronunciations) > 1

    def __iter__(self):
        """Enable tuple unpacking: hanzi, pinyins = hanzi_pinyin_obj"""
        return iter((self.character, self.pronunciations))

    def __getitem__(self, index: int):
        """Enable index access for backward compatibility."""
        if index == 0:
            return self.character
        elif index == 1:
            return self.pronunciations
        else:
            raise IndexError("HanziPinyin index out of range")


PINYIN_MAPPING_TABLE = get_pinyin_table_with_mapping_table()


@lru_cache(maxsize=1)
def get_has_single_pinyin_hanzi() -> List[HanziPinyin]:
    """Get all characters with single pinyin pronunciation.

    Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
    Usage: for hanzi, pinyins in get_has_single_pinyin_hanzi()

    Cached for performance as this is computed from static data.
    """
    return [
        HanziPinyin(character=hanzi, pronunciations=pinyins)
        for hanzi, pinyins in PINYIN_MAPPING_TABLE.items()
        if len(pinyins) == 1
    ]


@lru_cache(maxsize=1)
def get_has_multiple_pinyin_hanzi() -> List[HanziPinyin]:
    """Get all characters with multiple pinyin pronunciations.

    Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
    Usage: for hanzi, pinyins in get_has_multiple_pinyin_hanzi()

    Cached for performance as this is computed from static data.
    """
    return [
        HanziPinyin(character=hanzi, pronunciations=pinyins)
        for hanzi, pinyins in PINYIN_MAPPING_TABLE.items()
        if len(pinyins) > 1
    ]


# Modern, cleaner versions using the HanziPinyin dataclass
def get_single_pronunciation_characters() -> List[HanziPinyin]:
    """Get all characters with single pinyin pronunciation."""
    return [
        HanziPinyin(character=hanzi, pronunciations=pinyins)
        for hanzi, pinyins in PINYIN_MAPPING_TABLE.items()
        if len(pinyins) == 1
    ]


def get_multiple_pronunciation_characters() -> List[HanziPinyin]:
    """Get all characters with multiple pinyin pronunciations."""
    return [
        HanziPinyin(character=hanzi, pronunciations=pinyins)
        for hanzi, pinyins in PINYIN_MAPPING_TABLE.items()
        if len(pinyins) > 1
    ]


def iter_single_pinyin_hanzi() -> Iterator[HanziPinyin]:
    """Memory-efficient generator for characters with single pronunciation.

    Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
    Usage: for hanzi, pinyins in iter_single_pinyin_hanzi()
    """
    for hanzi, pinyins in PINYIN_MAPPING_TABLE.items():
        if len(pinyins) == 1:
            yield HanziPinyin(character=hanzi, pronunciations=pinyins)


def iter_multiple_pinyin_hanzi() -> Iterator[HanziPinyin]:
    """Memory-efficient generator for characters with multiple pronunciations.

    Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
    Usage: for hanzi, pinyins in iter_multiple_pinyin_hanzi()
    """
    for hanzi, pinyins in PINYIN_MAPPING_TABLE.items():
        if len(pinyins) > 1:
            yield HanziPinyin(character=hanzi, pronunciations=pinyins)


def iter_all_hanzi_with_filter(min_pinyin_count: int = 1) -> Iterator[HanziPinyin]:
    """Flexible generator to iterate over hanzi with configurable filtering.

    Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
    Usage: for hanzi, pinyins in iter_all_hanzi_with_filter(2)
    """
    for hanzi, pinyins in PINYIN_MAPPING_TABLE.items():
        if len(pinyins) >= min_pinyin_count:
            yield HanziPinyin(character=hanzi, pronunciations=pinyins)


# Modern generator versions using HanziPinyin dataclass
def iter_single_pronunciation_characters() -> Iterator[HanziPinyin]:
    """Memory-efficient generator for characters with single pronunciation."""
    for hanzi, pinyins in PINYIN_MAPPING_TABLE.items():
        if len(pinyins) == 1:
            yield HanziPinyin(character=hanzi, pronunciations=pinyins)


def iter_multiple_pronunciation_characters() -> Iterator[HanziPinyin]:
    """Memory-efficient generator for characters with multiple pronunciations."""
    for hanzi, pinyins in PINYIN_MAPPING_TABLE.items():
        if len(pinyins) > 1:
            yield HanziPinyin(character=hanzi, pronunciations=pinyins)


def iter_characters_by_pronunciation_count(
    min_count: int = 1, max_count: int = None
) -> Iterator[HanziPinyin]:
    """Flexible generator with pronunciation count filtering."""
    for hanzi, pinyins in PINYIN_MAPPING_TABLE.items():
        pronunciation_count = len(pinyins)
        if pronunciation_count >= min_count:
            if max_count is None or pronunciation_count <= max_count:
                yield HanziPinyin(character=hanzi, pronunciations=pinyins)
