# -*- coding: utf-8 -*-
"""Data processing module for pinyin and character mappings."""

from __future__ import annotations

from .character_data import (
    CharacterDataManager,
    CharacterInfo,
    get_default_character_manager,
)
from .mapping_data import MappingDataManager, get_default_mapping_manager
from .pinyin_data import PinyinDataManager, get_default_pinyin_manager

__all__ = [
    "PinyinDataManager",
    "CharacterDataManager",
    "CharacterInfo",
    "MappingDataManager",
    "get_default_pinyin_manager",
    "get_default_character_manager",
    "get_default_mapping_manager",
]
