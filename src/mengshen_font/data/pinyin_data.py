# -*- coding: utf-8 -*-
"""Pinyin data management with clean architecture."""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional, Protocol

from ..config import ProjectPaths, FontConstants


class PinyinDataSource(Protocol):
    """Protocol for pinyin data sources."""
    
    def get_pinyin(self, hanzi: str) -> Optional[List[str]]:
        """Get pinyin pronunciations for a character."""
        ...
    
    def get_all_mappings(self) -> Dict[str, List[str]]:
        """Get all character to pinyin mappings."""
        ...


class OfflinePinyinDataSource:
    """Offline pinyin data source using processed mapping table."""
    
    def __init__(self, paths: Optional[ProjectPaths] = None):
        """Initialize with project paths."""
        self.paths = paths or ProjectPaths()
        self._data: Optional[Dict[str, List[str]]] = None
    
    def _load_data(self) -> None:
        """Load pinyin mapping data from merged-mapping-table.txt."""
        if self._data is not None:
            return
        
        merged_file = self.paths.get_output_path("merged-mapping-table.txt")
        
        if not merged_file.exists():
            raise FileNotFoundError(f"Merged mapping table not found: {merged_file}")
        
        self._data = {}
        
        with open(merged_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Parse format: U+4E2D: zhōng,zhòng  # 中
                parts = line.split(':')
                if len(parts) < 2:
                    continue
                
                str_unicode = parts[0].strip()
                int_unicode = int(str_unicode[2:], 16)
                hanzi = chr(int_unicode)
                
                # Extract pinyin part (before comment if any)
                pinyin_part = parts[1].split('#')[0].strip()
                if pinyin_part:
                    pinyins = [p.strip() for p in pinyin_part.split(',') if p.strip()]
                    if pinyins:
                        self._data[hanzi] = pinyins
    
    def get_pinyin(self, hanzi: str) -> Optional[List[str]]:
        """Get pinyin pronunciations for a character."""
        self._load_data()
        return self._data.get(hanzi)
    
    def get_all_mappings(self) -> Dict[str, List[str]]:
        """Get all character to pinyin mappings."""
        self._load_data()
        return self._data.copy()


class PinyinDataManager:
    """Manages pinyin data access with pluggable data sources."""
    
    def __init__(self, data_source: Optional[PinyinDataSource] = None):
        """Initialize with optional data source."""
        self._data_source = data_source or OfflinePinyinDataSource()
    
    @lru_cache(maxsize=FontConstants.LRU_CACHE_SIZE_LARGE)
    def get_pinyin(self, hanzi: str) -> Optional[List[str]]:
        """Get pinyin pronunciations for a character (cached)."""
        return self._data_source.get_pinyin(hanzi)
    
    def get_all_mappings(self) -> Dict[str, List[str]]:
        """Get all character to pinyin mappings."""
        return self._data_source.get_all_mappings()
    
    def has_multiple_pronunciations(self, hanzi: str) -> bool:
        """Check if character has multiple pronunciations."""
        pinyins = self.get_pinyin(hanzi)
        return pinyins is not None and len(pinyins) > 1
    
    def has_single_pronunciation(self, hanzi: str) -> bool:
        """Check if character has single pronunciation."""
        pinyins = self.get_pinyin(hanzi)
        return pinyins is not None and len(pinyins) == 1
    
    def get_character_count(self) -> int:
        """Get total number of characters with pinyin data."""
        return len(self.get_all_mappings())
    
    def get_homograph_count(self) -> int:
        """Get number of characters with multiple pronunciations."""
        return sum(1 for pinyins in self.get_all_mappings().values() if len(pinyins) > 1)


# Global instance for backward compatibility
_default_manager: Optional[PinyinDataManager] = None


def get_default_pinyin_manager() -> PinyinDataManager:
    """Get the default pinyin data manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = PinyinDataManager()
    return _default_manager


# Backward compatibility functions
def get_pinyin_table_with_mapping_table() -> Dict[str, List[str]]:
    """Backward compatibility function for legacy code."""
    return get_default_pinyin_manager().get_all_mappings()