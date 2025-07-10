# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Legacy utility functions migrated to refactored architecture.

This module contains all utility functions from the original src/utility.py,
migrated to work independently in the refactored architecture while preserving
all original comments and functionality.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterator, List, Dict, Any
from dataclasses import dataclass

from ..data.pinyin_data import PinyinDataManager


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


# ピンイン表記の簡略化、e.g.: wěi -> we3i
SIMPLED_ALPHABET = {
    "a":"a", "ā":"a1", "á":"a2", "ǎ":"a3", "à":"a4",
    "b":"b",
    "c":"c",
    "d":"d",
    "e":"e", "ē":"e1", "é":"e2", "ě":"e3", "è":"e4",
    "f":"f",
    "g":"g",
    "h":"h",
    "i":"i", "ī":"i1", "í":"i2", "ǐ":"i3", "ì":"i4",
    "j":"j",
    "k":"k",
    "l":"l",
    "m":"m", "m̄":"m1", "ḿ":"m2", "m̀":"m4",
    "n":"n",           "ń":"n2", "ň":"n3", "ǹ":"n4",
    "o":"o", "ō":"o1", "ó":"o2", "ǒ":"o3", "ò":"o4",
    "p":"p",
    "q":"q",
    "r":"r",
    "s":"s",
    "t":"t",
    "u":"u", "ū":"u1", "ú":"u2" ,"ǔ":"u3", "ù":"u4", "ü":"v", "ǖ":"v1", "ǘ":"v2", "ǚ":"v3", "ǜ":"v4",
    "v":"v",
    "w":"w",
    "x":"x",
    "y":"y",
    "z":"z"
}


class LegacyUtility:
    """
    Migrated utility functions from src/utility.py with full independence.
    All original functionality and comments preserved.
    """
    
    def __init__(self, pinyin_data_manager: PinyinDataManager = None, template_main_path: str | None = None):
        """Initialize with optional pinyin data manager."""
        self._pinyin_manager = pinyin_data_manager or PinyinDataManager()
        self._cmap_table: Dict[str, str] = {}
        self._pinyin_mapping_table: Dict[str, List[str]] = {}
        self._template_main_path = template_main_path
        self._initialize_data()
    
    def _initialize_data(self) -> None:
        """Initialize pinyin mapping table from data manager."""
        self._pinyin_mapping_table = self._pinyin_manager.get_all_mappings()
    
    def get_cmap_table(self) -> None:
        """Load cmap table from template JSON file."""
        # Load cmap table from template_main.json
        import orjson
        from pathlib import Path
        
        if not self._template_main_path:
            raise ValueError("Template main path is not set in LegacyUtility")

        template_path = Path(self._template_main_path)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        try:
            with open(template_path, "rb") as f:
                template_data = orjson.loads(f.read())
            
            if "cmap" not in template_data:
                raise KeyError("No 'cmap' section found in template file")
            
            self._cmap_table = template_data["cmap"]
            
        except Exception as e:
            raise RuntimeError(f"Failed to load cmap table from {template_path}: {e}")
    
    # ピンイン表記の簡略化、e.g.: wěi -> we3i
    @lru_cache(maxsize=1024)
    def simplification_pronunciation(self, pronunciation: str) -> str:
        """Simplify pinyin pronunciation with caching for performance."""
        return "".join([SIMPLED_ALPHABET[c] for c in pronunciation])
    
    @lru_cache(maxsize=1)
    def get_has_single_pinyin_hanzi(self) -> List[HanziPinyin]:
        """Get all characters with single pinyin pronunciation.
        
        Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
        Usage: for hanzi, pinyins in get_has_single_pinyin_hanzi()
        
        Cached for performance as this is computed from static data.
        """
        return [
            HanziPinyin(character=hanzi, pronunciations=pinyins)
            for hanzi, pinyins in self._pinyin_mapping_table.items()
            if len(pinyins) == 1
        ]
    
    @lru_cache(maxsize=1)
    def get_has_multiple_pinyin_hanzi(self) -> List[HanziPinyin]:
        """Get all characters with multiple pinyin pronunciations.
        
        Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
        Usage: for hanzi, pinyins in get_has_multiple_pinyin_hanzi()
        
        Cached for performance as this is computed from static data.
        """
        return [
            HanziPinyin(character=hanzi, pronunciations=pinyins)
            for hanzi, pinyins in self._pinyin_mapping_table.items()
            if len(pinyins) > 1
        ]
    
    # Modern, cleaner versions using the HanziPinyin dataclass
    def get_single_pronunciation_characters(self) -> List[HanziPinyin]:
        """Get all characters with single pinyin pronunciation."""
        return [
            HanziPinyin(character=hanzi, pronunciations=pinyins)
            for hanzi, pinyins in self._pinyin_mapping_table.items()
            if len(pinyins) == 1
        ]
    
    def get_multiple_pronunciation_characters(self) -> List[HanziPinyin]:
        """Get all characters with multiple pinyin pronunciations."""
        return [
            HanziPinyin(character=hanzi, pronunciations=pinyins)
            for hanzi, pinyins in self._pinyin_mapping_table.items()
            if len(pinyins) > 1
        ]
    
    def iter_single_pinyin_hanzi(self) -> Iterator[HanziPinyin]:
        """Memory-efficient generator for characters with single pronunciation.
        
        Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
        Usage: for hanzi, pinyins in iter_single_pinyin_hanzi()
        """
        for hanzi, pinyins in self._pinyin_mapping_table.items():
            if len(pinyins) == 1:
                yield HanziPinyin(character=hanzi, pronunciations=pinyins)
    
    def iter_multiple_pinyin_hanzi(self) -> Iterator[HanziPinyin]:
        """Memory-efficient generator for characters with multiple pronunciations.
        
        Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
        Usage: for hanzi, pinyins in iter_multiple_pinyin_hanzi()
        """
        for hanzi, pinyins in self._pinyin_mapping_table.items():
            if len(pinyins) > 1:
                yield HanziPinyin(character=hanzi, pronunciations=pinyins)
    
    def iter_all_hanzi_with_filter(self, min_pinyin_count: int = 1) -> Iterator[HanziPinyin]:
        """Flexible generator to iterate over hanzi with configurable filtering.
        
        Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
        Usage: for hanzi, pinyins in iter_all_hanzi_with_filter(2)
        """
        for hanzi, pinyins in self._pinyin_mapping_table.items():
            if len(pinyins) >= min_pinyin_count:
                yield HanziPinyin(character=hanzi, pronunciations=pinyins)
    
    # Modern generator versions using HanziPinyin dataclass
    def iter_single_pronunciation_characters(self) -> Iterator[HanziPinyin]:
        """Memory-efficient generator for characters with single pronunciation."""
        for hanzi, pinyins in self._pinyin_mapping_table.items():
            if len(pinyins) == 1:
                yield HanziPinyin(character=hanzi, pronunciations=pinyins)
    
    def iter_multiple_pronunciation_characters(self) -> Iterator[HanziPinyin]:
        """Memory-efficient generator for characters with multiple pronunciations."""
        for hanzi, pinyins in self._pinyin_mapping_table.items():
            if len(pinyins) > 1:
                yield HanziPinyin(character=hanzi, pronunciations=pinyins)
    
    def iter_characters_by_pronunciation_count(self, min_count: int = 1, max_count: int = None) -> Iterator[HanziPinyin]:
        """Flexible generator with pronunciation count filtering."""
        for hanzi, pinyins in self._pinyin_mapping_table.items():
            pronunciation_count = len(pinyins)
            if pronunciation_count >= min_count:
                if max_count is None or pronunciation_count <= max_count:
                    yield HanziPinyin(character=hanzi, pronunciations=pinyins)
    
    # 漢字から cid を取得する
    @lru_cache(maxsize=2048)
    def convert_str_hanzi_2_cid(self, str_hanzi: str) -> str:
        """Convert hanzi character to CID with caching for performance."""
        if len(self._cmap_table) == 0:
            self.get_cmap_table()
        
        unicode_value = str(ord(str_hanzi))
        if unicode_value not in self._cmap_table:
            raise KeyError(f"Character '{str_hanzi}' (U+{ord(str_hanzi):04X}, code={unicode_value}) not found in cmap table")
        
        return self._cmap_table[unicode_value]
    
    # [階層構造のあるdictをupdateする](https://www.greptips.com/posts/1242/)
    def deepupdate(self, dict_base: Dict[str, Any], other: Dict[str, Any]) -> None:
        """Update nested dictionary structure recursively."""
        for k, v in other.items():
            if isinstance(v, dict) and k in dict_base:
                self.deepupdate(dict_base[k], v)
            else:
                dict_base[k] = v

