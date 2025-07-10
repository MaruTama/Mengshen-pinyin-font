# -*- coding: utf-8 -*-
"""
Mengshen Font Utilities Module

This module contains utility functions for handling Chinese characters,
pinyin processing, and font operations.
"""

from .hanzi_pinyin import (
    HanziPinyin,
    get_has_single_pinyin_hanzi,
    get_has_multiple_pinyin_hanzi,
    get_single_pronunciation_characters,
    get_multiple_pronunciation_characters,
    iter_single_pinyin_hanzi,
    iter_multiple_pinyin_hanzi,
    iter_all_hanzi_with_filter,
    iter_single_pronunciation_characters,
    iter_multiple_pronunciation_characters,
    iter_characters_by_pronunciation_count,
)

from .pinyin_conversion import (
    SIMPLED_ALPHABET,
    simplification_pronunciation,
)

from .cmap_utils import (
    convert_str_hanzi_2_cid,
    get_cmap_table,
)

from .dict_utils import (
    deepupdate,
)

__all__ = [
    'HanziPinyin',
    'SIMPLED_ALPHABET',
    'simplification_pronunciation',
    'get_has_single_pinyin_hanzi',
    'get_has_multiple_pinyin_hanzi',
    'get_single_pronunciation_characters',
    'get_multiple_pronunciation_characters',
    'iter_single_pinyin_hanzi',
    'iter_multiple_pinyin_hanzi',
    'iter_all_hanzi_with_filter',
    'iter_single_pronunciation_characters',
    'iter_multiple_pronunciation_characters',
    'iter_characters_by_pronunciation_count',
    'convert_str_hanzi_2_cid',
    'deepupdate',
    'get_cmap_table',
]