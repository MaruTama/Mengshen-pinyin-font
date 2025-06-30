# -*- coding: utf-8 -*-
#!/usr/bin/env python

from __future__ import annotations

import os
import orjson
import pinyin_getter as pg
import path as p
from typing import Iterator, List, TypedDict, Dict, Any
from dataclasses import dataclass


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

cmap_table: Dict[str, str] = {}
PINYIN_MAPPING_TABLE = pg.get_pinyin_table_with_mapping_table()

def get_cmap_table() -> None:
    global cmap_table
    TAMPLATE_MAIN_JSON = os.path.join(p.DIR_TEMP, "template_main.json")
    with open(TAMPLATE_MAIN_JSON, "rb") as read_file:
        marged_font = orjson.loads(read_file.read())
    cmap_table = marged_font["cmap"]

# ピンイン表記の簡略化、e.g.: wěi -> we3i
def simplification_pronunciation(pronunciation: str) -> str:
    return  "".join( [SIMPLED_ALPHABET[c] for c in pronunciation] )

def get_has_single_pinyin_hanzi() -> List[HanziPinyin]:
    """Get all characters with single pinyin pronunciation.
    
    Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
    Usage: for hanzi, pinyins in get_has_single_pinyin_hanzi()
    """
    return [
        HanziPinyin(character=hanzi, pronunciations=pinyins)
        for hanzi, pinyins in PINYIN_MAPPING_TABLE.items()
        if len(pinyins) == 1
    ]

def get_has_multiple_pinyin_hanzi() -> List[HanziPinyin]:
    """Get all characters with multiple pinyin pronunciations.
    
    Returns HanziPinyin objects that support tuple unpacking for backward compatibility.
    Usage: for hanzi, pinyins in get_has_multiple_pinyin_hanzi()
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

def iter_characters_by_pronunciation_count(min_count: int = 1, max_count: int = None) -> Iterator[HanziPinyin]:
    """Flexible generator with pronunciation count filtering."""
    for hanzi, pinyins in PINYIN_MAPPING_TABLE.items():
        pronunciation_count = len(pinyins)
        if pronunciation_count >= min_count:
            if max_count is None or pronunciation_count <= max_count:
                yield HanziPinyin(character=hanzi, pronunciations=pinyins)

# 漢字から cid を取得する
def convert_str_hanzi_2_cid(str_hanzi: str) -> str:
    if len(cmap_table) == 0:
        get_cmap_table()
    return cmap_table[ str(ord(str_hanzi)) ]

# [階層構造のあるdictをupdateする](https://www.greptips.com/posts/1242/)
def deepupdate(dict_base: Dict[str, Any], other: Dict[str, Any]) -> None:
    for k, v in other.items():
        if isinstance(v, dict) and k in dict_base:
            deepupdate(dict_base[k], v)
        else:
            dict_base[k] = v