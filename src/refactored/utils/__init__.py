# -*- coding: utf-8 -*-
"""
Mengshen Font Utilities Module

This module contains utility functions for handling Chinese characters,
pinyin processing, and font operations.
"""

from .cmap_utils import convert_str_hanzi_2_cid, get_cmap_table
from .dict_utils import deep_update


# Use lazy imports to avoid circular dependencies
def __getattr__(name: str):
    """Lazy import for circular dependency resolution."""
    if name in [
        "HanziPinyin",
        "get_has_multiple_pinyin_hanzi",
        "get_has_single_pinyin_hanzi",
        "get_multiple_pronunciation_characters",
        "get_single_pronunciation_characters",
        "iter_all_hanzi_with_filter",
        "iter_characters_by_pronunciation_count",
        "iter_multiple_pinyin_hanzi",
        "iter_multiple_pronunciation_characters",
        "iter_single_pinyin_hanzi",
        "iter_single_pronunciation_characters",
    ]:
        return locals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


from .pinyin_utils import PINYIN_TONE_TO_NUMERIC, simplification_pronunciation
from .shell_utils import SecurityError, ShellExecutor, safe_command_execution

__all__ = [
    "HanziPinyin",
    "PINYIN_TONE_TO_NUMERIC",
    "simplification_pronunciation",
    "get_has_single_pinyin_hanzi",
    "get_has_multiple_pinyin_hanzi",
    "get_single_pronunciation_characters",
    "get_multiple_pronunciation_characters",
    "iter_single_pinyin_hanzi",
    "iter_multiple_pinyin_hanzi",
    "iter_all_hanzi_with_filter",
    "iter_single_pronunciation_characters",
    "iter_multiple_pronunciation_characters",
    "iter_characters_by_pronunciation_count",
    "convert_str_hanzi_2_cid",
    "deep_update",
    "get_cmap_table",
    "ShellExecutor",
    "safe_command_execution",
    "SecurityError",
]
