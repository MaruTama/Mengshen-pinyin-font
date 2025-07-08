# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Legacy configuration migrated from src/config.py

This module contains all configuration settings from the original src/config.py,
migrated to work independently in the refactored architecture while preserving
all original comments and functionality.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path


class FontType(IntEnum):
    """Font type enumeration for type safety."""
    HAN_SERIF = 1
    HANDWRITTEN = 2


# Backward compatibility
HAN_SERIF_TYPE = FontType.HAN_SERIF
HANDWRITTEN_TYPE = FontType.HANDWRITTEN


@dataclass(frozen=True)
class PinyinCanvas:
    """Configuration for pinyin display area."""
    width: float
    height: float
    base_line: float
    tracking: float
    scale: float = 1.0  # 拼音の縮尺（1.0 = 100%、0.8 = 80%）


@dataclass(frozen=True)
class HanziCanvas:
    """Configuration for hanzi display area."""
    width: int
    height: int


@dataclass(frozen=True)
class FontMetadata:
    """Metadata configuration for font rendering."""
    pinyin_canvas: PinyinCanvas
    expected_hanzi_canvas: HanziCanvas
    is_avoid_overlapping_mode: bool
    x_scale_reduction_for_avoid_overlapping: float


# metadata for font size
METADATA_FOR_HAN_SERIF = FontMetadata(
    pinyin_canvas=PinyinCanvas(
        width=850,      # ピンイン表示部の幅
        height=283.3,   # ピンイン表示部の高さ
        base_line=935,  # ベースラインからの高さ
        tracking=22.145, # 拼音の標準空白幅： Tracking is about uniform spacing across a text selection.
        scale=1.0       # 拼音の縮尺（han_serif用）
    ),
    expected_hanzi_canvas=HanziCanvas(
        width=1000,  # 基準にする漢字の表示部の幅
        height=1000, # 基準にする漢字の表示部の高さ
    ),
    # ピンインが 5~6 文字以上(最大は6のはず)のとき、文字が重なることがある。この時にx軸を縮小して重なりを避けるモード
    is_avoid_overlapping_mode=False,
    x_scale_reduction_for_avoid_overlapping=0.1 # 上記のモードの際に x軸をどれだけ縮小するか
)

METADATA_FOR_HANDWRITTEN = FontMetadata(
    pinyin_canvas=PinyinCanvas(
        width=800,    # ピンイン表示部の幅
        height=300,   # ピンイン表示部の高さ
        base_line=880, # ベースラインからの高さ (corrected for handwritten)
        tracking=5,   # 拼音の標準空白幅： Tracking is about uniform spacing across a text selection.
        scale=0.9     # 拼音の縮尺（handwritten用、90%に縮小）
    ),
    expected_hanzi_canvas=HanziCanvas(
        width=1000,  # 基準にする漢字の表示部の幅
        height=1000, # 基準にする漢字の表示部の高さ
    ),
    # ピンインが 5~6 文字以上(最大は6のはず)のとき、文字が重なることがある。この時にx軸を縮小して重なりを避けるモード
    is_avoid_overlapping_mode=True,
    x_scale_reduction_for_avoid_overlapping=0.1 # 上記のモードの際に x軸をどれだけ縮小するか
)


class LegacyPaths:
    """Legacy path definitions for font files."""
    
    @staticmethod
    def get_project_root() -> Path:
        """Get project root directory."""
        # Get the directory containing this file, then go up to project root
        current_file = Path(__file__)
        return current_file.parent.parent.parent.parent
    
    @staticmethod
    def get_font_dir() -> Path:
        """Get base font directory."""
        return LegacyPaths.get_project_root() / "res" / "fonts"
    
    @staticmethod
    def get_han_serif_dir() -> Path:
        """Get han-serif font directory."""
        return LegacyPaths.get_font_dir() / "han-serif"
    
    @staticmethod
    def get_handwritten_dir() -> Path:
        """Get handwritten font directory."""
        return LegacyPaths.get_font_dir() / "handwritten"
    
    @staticmethod
    def get_temp_dir() -> Path:
        """Get temporary directory."""
        return LegacyPaths.get_project_root() / "tmp"


# using font name
def get_han_serif_main_font_path() -> str:
    """Get HAN_SERIF main font path."""
    return str(LegacyPaths.get_han_serif_dir() / "SourceHanSerifCN-Regular.ttf")

def get_han_serif_pinyin_font_path() -> str:
    """Get HAN_SERIF pinyin font path."""
    return str(LegacyPaths.get_han_serif_dir() / "mplus-1m-medium.ttf")

def get_handwritten_main_font_path() -> str:
    """Get HANDWRITTEN main font path."""
    return str(LegacyPaths.get_handwritten_dir() / "XiaolaiMonoSC-without-Hangul-Regular.ttf")

def get_handwritten_pinyin_font_path() -> str:
    """Get HANDWRITTEN pinyin font path."""
    return str(LegacyPaths.get_handwritten_dir() / "latin-alpabet-of-SetoFont-SP.ttf")


# Legacy compatibility - maintain original variable names
HAN_SERIF_MAIN = get_han_serif_main_font_path()
HAN_SERIF_PINYIN = get_han_serif_pinyin_font_path()
HAN_HANDWRITTEN_MAIN = get_handwritten_main_font_path()
HAN_HANDWRITTEN_PINYIN = get_handwritten_pinyin_font_path()


class LegacyConfigManager:
    """Manager for legacy configuration with full backward compatibility."""
    
    @staticmethod
    def get_font_metadata(font_type: FontType) -> FontMetadata:
        """Get font metadata by type."""
        if font_type == FontType.HAN_SERIF:
            return METADATA_FOR_HAN_SERIF
        elif font_type == FontType.HANDWRITTEN:
            return METADATA_FOR_HANDWRITTEN
        else:
            raise ValueError(f"Unknown font type: {font_type}")
    
    @staticmethod
    def get_main_font_path(font_type: FontType) -> str:
        """Get main font path by type."""
        if font_type == FontType.HAN_SERIF:
            return get_han_serif_main_font_path()
        elif font_type == FontType.HANDWRITTEN:
            return get_handwritten_main_font_path()
        else:
            raise ValueError(f"Unknown font type: {font_type}")
    
    @staticmethod
    def get_pinyin_font_path(font_type: FontType) -> str:
        """Get pinyin font path by type."""
        if font_type == FontType.HAN_SERIF:
            return get_han_serif_pinyin_font_path()
        elif font_type == FontType.HANDWRITTEN:
            return get_handwritten_pinyin_font_path()
        else:
            raise ValueError(f"Unknown font type: {font_type}")
    
    @staticmethod
    def get_pinyin_canvas(font_type: FontType) -> PinyinCanvas:
        """Get pinyin canvas configuration by type."""
        metadata = LegacyConfigManager.get_font_metadata(font_type)
        return metadata.pinyin_canvas
    
    @staticmethod
    def get_hanzi_canvas(font_type: FontType) -> HanziCanvas:
        """Get hanzi canvas configuration by type."""
        metadata = LegacyConfigManager.get_font_metadata(font_type)
        return metadata.expected_hanzi_canvas


# Legacy function exports for backward compatibility
def get_metadata_for_han_serif() -> FontMetadata:
    """Legacy function wrapper."""
    return METADATA_FOR_HAN_SERIF

def get_metadata_for_handwritten() -> FontMetadata:
    """Legacy function wrapper."""
    return METADATA_FOR_HANDWRITTEN