# -*- coding: utf-8 -*-
"""
Offline pinyin data loader for mozillazg/pinyin-data.

This module provides secure, offline alternatives to web scraping,
eliminating external dependencies and security vulnerabilities.
"""

from __future__ import annotations

import re
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class PinyinEntry:
    """Represents a single character's pinyin pronunciation data."""
    unicode_point: str
    character: str
    pronunciations: List[str]
    
    @property
    def is_multiple_pronunciation(self) -> bool:
        """Check if character has multiple pronunciations (homograph)."""
        return len(self.pronunciations) > 1


class OfflinePinyinLoader:
    """
    Loads pinyin data from git submodule without web requests.
    
    Provides backward compatibility with existing pinyin_getter functions
    while eliminating security vulnerabilities from web scraping.
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize the offline pinyin loader.
        
        Args:
            data_path: Path to pinyin-data directory. If None, uses default location.
        """
        if data_path is None:
            self.data_path = Path(__file__).parent.parent / "res" / "phonics" / "pinyin-data"
        else:
            self.data_path = Path(data_path)
        
        # Lazy loading - data loaded on first access
        self._pinyin_mapping: Optional[Dict[str, List[str]]] = None
        self._unicode_mapping: Optional[Dict[str, str]] = None
        
    def _ensure_data_loaded(self) -> None:
        """Ensure pinyin data is loaded (lazy loading)."""
        if self._pinyin_mapping is None:
            self._load_pinyin_data()
    
    def _load_pinyin_data(self) -> None:
        """Load pinyin data from pinyin.txt file."""
        pinyin_file = self.data_path / "pinyin.txt"
        
        if not pinyin_file.exists():
            raise FileNotFoundError(f"Pinyin data file not found: {pinyin_file}")
        
        self._pinyin_mapping = {}
        self._unicode_mapping = {}
        
        # Parse format: U+4E2D: zhōng,zhòng  # 中
        pattern = re.compile(r'^U\+([0-9A-F]+):\s*([^#]+)\s*#\s*(.*)$')
        
        with open(pinyin_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                match = pattern.match(line)
                if not match:
                    # Skip malformed lines silently (some data may have variations)
                    continue
                
                unicode_hex, pinyin_str, char = match.groups()
                
                # Parse pronunciations
                pronunciations = [p.strip() for p in pinyin_str.split(',') if p.strip()]
                
                if char and pronunciations:
                    self._pinyin_mapping[char] = pronunciations
                    self._unicode_mapping[char] = f"U+{unicode_hex}"
    
    @lru_cache(maxsize=2048)
    def get_pinyin(self, hanzi: str) -> Optional[List[str]]:
        """
        Get pinyin pronunciations for a Chinese character.
        
        Args:
            hanzi: Chinese character
            
        Returns:
            List of pinyin pronunciations, or None if not found
        """
        self._ensure_data_loaded()
        return self._pinyin_mapping.get(hanzi)
    
    def get_pinyin_entry(self, hanzi: str) -> Optional[PinyinEntry]:
        """
        Get complete pinyin entry for a character.
        
        Args:
            hanzi: Chinese character
            
        Returns:
            PinyinEntry object or None if not found
        """
        self._ensure_data_loaded()
        pronunciations = self._pinyin_mapping.get(hanzi)
        unicode_point = self._unicode_mapping.get(hanzi)
        
        if pronunciations and unicode_point:
            return PinyinEntry(
                unicode_point=unicode_point,
                character=hanzi,
                pronunciations=pronunciations
            )
        return None
    
    def iter_all_characters(self) -> Iterator[PinyinEntry]:
        """
        Memory-efficient iterator over all characters with pinyin data.
        
        Yields:
            PinyinEntry objects for all characters
        """
        self._ensure_data_loaded()
        for char, pronunciations in self._pinyin_mapping.items():
            unicode_point = self._unicode_mapping.get(char, "")
            yield PinyinEntry(
                unicode_point=unicode_point,
                character=char,
                pronunciations=pronunciations
            )
    
    def iter_homographs(self) -> Iterator[PinyinEntry]:
        """
        Memory-efficient iterator over characters with multiple pronunciations.
        
        Yields:
            PinyinEntry objects for homograph characters only
        """
        for entry in self.iter_all_characters():
            if entry.is_multiple_pronunciation:
                yield entry
    
    def get_character_count(self) -> int:
        """Get total number of characters in the dataset."""
        self._ensure_data_loaded()
        return len(self._pinyin_mapping)
    
    def get_homograph_count(self) -> int:
        """Get number of characters with multiple pronunciations."""
        return sum(1 for _ in self.iter_homographs())
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get dataset statistics.
        
        Returns:
            Dictionary with character counts and statistics
        """
        self._ensure_data_loaded()
        
        total_chars = self.get_character_count()
        homograph_count = self.get_homograph_count()
        single_pronunciation_count = total_chars - homograph_count
        
        return {
            'total_characters': total_chars,
            'single_pronunciation': single_pronunciation_count,
            'multiple_pronunciation': homograph_count,
            'homograph_percentage': round((homograph_count / total_chars) * 100, 2) if total_chars > 0 else 0
        }


# Global instance for backward compatibility
_default_loader: Optional[OfflinePinyinLoader] = None


def get_offline_pinyin_loader() -> OfflinePinyinLoader:
    """Get the default offline pinyin loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = OfflinePinyinLoader()
    return _default_loader


def get_pinyin_offline(hanzi: str) -> Optional[List[str]]:
    """
    Backward-compatible function to get pinyin pronunciations.
    
    This function replaces web scraping calls with offline data access.
    
    Args:
        hanzi: Chinese character
        
    Returns:
        List of pinyin pronunciations, or None if not found
    """
    return get_offline_pinyin_loader().get_pinyin(hanzi)


def create_offline_mapping_table() -> Dict[str, List[str]]:
    """
    Create a mapping table compatible with existing code.
    
    Returns:
        Dictionary mapping characters to their pronunciations
    """
    loader = get_offline_pinyin_loader()
    loader._ensure_data_loaded()
    return loader._pinyin_mapping.copy()