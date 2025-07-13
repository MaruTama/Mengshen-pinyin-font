# -*- coding: utf-8 -*-
"""Font configuration management with type safety."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Dict


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


# Backward compatibility constants
HAN_SERIF_TYPE = FontType.HAN_SERIF
HANDWRITTEN_TYPE = FontType.HANDWRITTEN

# Legacy metadata access (deprecated - use FontConfig class instead)
METADATA_FOR_PINYIN = {
    FontType.HAN_SERIF: FontConfig.get_config(FontType.HAN_SERIF),
    FontType.HANDWRITTEN: FontConfig.get_config(FontType.HANDWRITTEN),
}
