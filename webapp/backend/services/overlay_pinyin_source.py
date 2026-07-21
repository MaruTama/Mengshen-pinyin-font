# -*- coding: utf-8 -*-
"""PinyinDataSource that merges project reading overrides into the base data.

Implements the PinyinDataSource protocol (src/refactored/data/pinyin_data.py)
so a per-project PinyinDataManager can be injected into FontBuilder.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from src.refactored.data.pinyin_data import MergedMappingPinyinDataSource

from ..schemas import Project


class OverlayPinyinDataSource:
    """Base mapping data with per-project replace/append overrides."""

    def __init__(self, project: Project):
        self._base = MergedMappingPinyinDataSource()
        self._overrides = project.glyph_overrides.readings
        self._excluded = set(project.glyph_overrides.excluded_characters)

    def get_pinyin(self, hanzi: str) -> Optional[List[str]]:
        if hanzi in self._excluded:
            return None
        base = self._base.get_pinyin(hanzi)
        override = self._overrides.get(hanzi)
        if override is None:
            return base
        if override.mode == "replace":
            return list(override.pronunciations)
        merged = list(base or [])
        merged.extend(p for p in override.pronunciations if p not in merged)
        return merged

    def get_all_mappings(self) -> Dict[str, List[str]]:
        mappings = dict(self._base.get_all_mappings())
        for char in self._excluded:
            mappings.pop(char, None)
        for char, override in self._overrides.items():
            if char in self._excluded:
                continue
            merged = self.get_pinyin(char)
            if merged:
                mappings[char] = merged
        return mappings
