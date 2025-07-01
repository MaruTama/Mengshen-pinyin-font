# -*- coding: utf-8 -*-
"""Font generation constants."""

from __future__ import annotations


class FontConstants:
    """Constants used throughout the font generation process."""
    
    # Pronunciation indices
    NORMAL_PRONUNCIATION = 0
    VARIATIONAL_PRONUNCIATION = 1
    
    # Stylistic set indices  
    SS_NORMAL_PRONUNCIATION = 1
    SS_VARIATIONAL_PRONUNCIATION = 2
    
    # Unicode IVS (Ideographic Variant Selector)
    IVS_BASE = 0xE01E0  # 917984
    
    # Font limits
    MAX_GLYPHS = 65536
    
    # File extensions
    TTF_EXTENSION = ".ttf"
    JSON_EXTENSION = ".json"
    TXT_EXTENSION = ".txt"
    
    # Font table names
    CMAP_TABLE = "cmap"
    CMAP_UVS_TABLE = "cmap_uvs" 
    GLYF_TABLE = "glyf"
    GSUB_TABLE = "GSUB"
    HEAD_TABLE = "head"
    HHEA_TABLE = "hhea"
    OS2_TABLE = "OS_2"
    NAME_TABLE = "name"
    GLYPH_ORDER = "glyph_order"
    
    # Duplicate definition handling
    DUPLICATE_WU4_UNICODES = [0x2E8E, 0x5140, 0xFA0C]  # ⺎兀兀
    DUPLICATE_HU4_UNICODES = [0x55C0, 0xFA0D]          # 嗀嗀
    
    # Performance settings
    LRU_CACHE_SIZE_SMALL = 128
    LRU_CACHE_SIZE_MEDIUM = 512
    LRU_CACHE_SIZE_LARGE = 1024
    LRU_CACHE_SIZE_XLARGE = 2048
    
    # Date/time constants
    FONT_EPOCH_BASE_DATE = "1904/01/01 00:00"
    DATE_FORMAT = "%Y/%m/%d %H:%M"