# -*- coding: utf-8 -*-
"""Font configuration management with type safety."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Dict

from .paths import HAN_SERIF_FONT_DIR, HANDWRITTEN_FONT_DIR


class FontType(IntEnum):
    """Font type enumeration for type safety."""

    HAN_SERIF = 1
    HANDWRITTEN = 2


@dataclass(frozen=True)
class PinyinCanvas:
    """Pinyin canvas configuration."""

    width: float
    height: float
    base_line: float
    tracking: float


@dataclass(frozen=True)
class HanziCanvas:
    """Hanzi canvas configuration."""

    width: float
    height: float


@dataclass(frozen=True)
class FontMetadata:
    """Font metadata configuration."""

    pinyin_canvas: PinyinCanvas
    hanzi_canvas: HanziCanvas
    is_avoid_overlapping_mode: bool
    x_scale_reduction_for_avoid_overlapping: float


class FontConstants:
    """Constants used throughout the font generation process."""

    # Font file paths
    HAN_SERIF_FONT_PATH = HAN_SERIF_FONT_DIR / "SourceHanSerifCN-Regular.ttf"
    HANDWRITTEN_FONT_PATH = (
        HANDWRITTEN_FONT_DIR / "XiaolaiMonoSC-without-Hangul-Regular.ttf"
    )

    # Alphabet font paths
    HAN_SERIF_ALPHABET_FONT_PATH = HAN_SERIF_FONT_DIR / "mplus-1m-medium.ttf"
    HANDWRITTEN_ALPHABET_FONT_PATH = (
        HANDWRITTEN_FONT_DIR / "latin-alphabet-of-SetoFont-SP.ttf"
    )

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

    # External tool timeout for font conversion (in seconds)
    CONVERSION_TIMEOUT_SECONDS = 60

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
    # 定義が重複している文字に関しては、基本的に同一のグリフが使われているはず
    # どれかがグリフに発音を追加したら無視する。
    # もし、別のグリフが用意されているなら、グリフ数削減のためにも参照を先を統一する。
    DUPLICATE_WU4_UNICODES = [
        0x2E8E,
        0x5140,
        0xFA0C,
    ]  # ⺎(U+2E8E) 兀(U+5140) 兀(U+FA0C)
    DUPLICATE_HU4_UNICODES = [0x55C0, 0xFA0D]  # 嗀(U+55C0) 嗀(U+FA0D)

    # Performance settings
    LRU_CACHE_SIZE_SMALL = 128
    LRU_CACHE_SIZE_MEDIUM = 512
    LRU_CACHE_SIZE_LARGE = 1024
    LRU_CACHE_SIZE_XLARGE = 2048

    # Date/time constants
    # TrueType fonts use a different epoch than Unix time (1904 vs 1970)
    FONT_EPOCH_BASE_DATE = "1904/01/01 00:00"
    DATE_FORMAT = "%Y/%m/%d %H:%M"


class FontConfig:
    """Centralized font configuration management."""

    # Font style configurations
    _CONFIGS: Dict[FontType, FontMetadata] = {
        FontType.HAN_SERIF: FontMetadata(
            pinyin_canvas=PinyinCanvas(
                width=850.0,  # ピンイン表示部の幅
                height=283.3,  # ピンイン表示部の高さ
                base_line=935.0,  # ベースラインからの高さ
                tracking=22.145,  # 拼音の標準空白幅： Tracking is about uniform spacing across a text selection.
            ),
            hanzi_canvas=HanziCanvas(
                width=1000.0,  # 基準にする漢字の表示部の幅
                height=1000.0,  # 基準にする漢字の表示部の高さ
            ),
            # ピンインが 5~6 文字以上(最大は6のはず)のとき、文字が重なることがある。この時にx軸を縮小して重なりを避けるモード
            is_avoid_overlapping_mode=False,  # han_serif では重なり回避モードを無効
            x_scale_reduction_for_avoid_overlapping=0.1,  # 上記のモードの際に x軸をどれだけ縮小するか
        ),
        FontType.HANDWRITTEN: FontMetadata(
            pinyin_canvas=PinyinCanvas(
                width=800.0,  # ピンイン表示部の幅
                height=300.0,  # ピンイン表示部の高さ
                base_line=880.0,  # ベースラインからの高さ (handwritten 用に修正)
                tracking=5.0,  # 拼音の標準空白幅： Tracking is about uniform spacing across a text selection.
            ),
            hanzi_canvas=HanziCanvas(
                width=1000.0,  # 基準にする漢字の表示部の幅
                height=1000.0,  # 基準にする漢字の表示部の高さ
            ),
            # ピンインが 5~6 文字以上(最大は6のはず)のとき、文字が重なることがある。この時にx軸を縮小して重なりを避けるモード
            is_avoid_overlapping_mode=True,  # handwritten では重なり回避モードを有効 - 文字配置に重要
            x_scale_reduction_for_avoid_overlapping=0.1,  # 上記のモードの際に x軸をどれだけ縮小するか
        ),
    }

    @classmethod
    def get_config(cls, font_type: FontType) -> FontMetadata:
        """Get configuration for specified font type."""
        if font_type not in cls._CONFIGS:
            raise ValueError(f"Unsupported font type: {font_type}")
        return cls._CONFIGS[font_type]

    @classmethod
    def get_pinyin_canvas(cls, font_type: FontType) -> PinyinCanvas:
        """Get pinyin canvas configuration for font type."""
        return cls.get_config(font_type).pinyin_canvas

    @classmethod
    def get_hanzi_canvas(cls, font_type: FontType) -> HanziCanvas:
        """Get hanzi canvas configuration for font type."""
        return cls.get_config(font_type).hanzi_canvas

    @classmethod
    def get_font_path(cls, font_type: FontType) -> Path:
        """Get main font file path for specified font type."""
        if font_type == FontType.HAN_SERIF:
            return FontConstants.HAN_SERIF_FONT_PATH
        if font_type == FontType.HANDWRITTEN:
            return FontConstants.HANDWRITTEN_FONT_PATH
        raise ValueError(f"Unsupported font type: {font_type}")

    @classmethod
    def get_alphabet_font_path(cls, font_type: FontType) -> Path:
        """Get alphabet font file path for specified font type."""
        if font_type == FontType.HAN_SERIF:
            return FontConstants.HAN_SERIF_ALPHABET_FONT_PATH
        if font_type == FontType.HANDWRITTEN:
            return FontConstants.HANDWRITTEN_ALPHABET_FONT_PATH
        raise ValueError(f"Unsupported font type: {font_type}")


# Backward compatibility constants
HAN_SERIF_TYPE = FontType.HAN_SERIF
HANDWRITTEN_TYPE = FontType.HANDWRITTEN

# Legacy metadata access (deprecated - use FontConfig class instead)
METADATA_FOR_PINYIN = {
    FontType.HAN_SERIF: FontConfig.get_config(FontType.HAN_SERIF),
    FontType.HANDWRITTEN: FontConfig.get_config(FontType.HANDWRITTEN),
}

# Legacy constants for backward compatibility
METADATA_FOR_HAN_SERIF = FontConfig.get_config(FontType.HAN_SERIF)
METADATA_FOR_HANDWRITTEN = FontConfig.get_config(FontType.HANDWRITTEN)
